"""Sample Parquet target stream class, which handles writing streams."""

from datetime import datetime
import csv
import gzip
import os
import shutil
from typing import List
import tempfile

from singer_sdk.sinks import Sink

from target_athena import athena
from target_athena import s3
from target_athena import utils
from target_athena import formats

class AthenaSink(Sink):
    """Athena target sink class."""

    DEFAULT_BATCH_SIZE_ROWS = 10000

    def __init__(
        self,
        target,
        stream_name,
        schema,
        key_properties,
    ):
        super().__init__(target=target, stream_name=stream_name, schema=schema, key_properties=key_properties)
        self._s3_client = None
        self._athena_client = None
        ddl = athena.generate_create_database_ddl(self.config["athena_database"])
        athena.execute_sql(ddl, self.athena_client)

    @property
    def s3_client(self):
        if not self._s3_client:
            self._s3_client = s3.create_client(self.config)
        return self._s3_client

    @property
    def athena_client(self):
        if not self._athena_client:
            self._athena_client = athena.create_client(self.config, self.logger)
        return self._athena_client
    
    @property
    def datetime_error_treatment(self):
        return self.config.get("datetime_error_treatment", "ERROR")

    def drain(self, records_to_drain: List[dict]) -> None:
        """Write any prepped records out and return only once fully written."""
        state = None
        headers = {}
        headers = self.schema["properties"].keys()

        object_format = self.config.get("object_format")
        delimiter = self.config.get("delimiter", ",")
        quotechar = self.config.get("quotechar", '"')

        # Use the system specific temp directory if no custom temp_dir provided
        temp_dir = os.path.expanduser(
            self.config.get("temp_dir", tempfile.gettempdir())
        )

        # Create temp_dir if not exists
        if temp_dir:
            os.makedirs(temp_dir, exist_ok=True)

        filenames = []
        now = datetime.now().strftime("%Y%m%dT%H%M%S")

        # Serialize records to local files
        for record in records_to_drain:
            filename = self.stream_name + "-" + now + "." + object_format
            filename = os.path.expanduser(os.path.join(temp_dir, filename))
            s3_prefix = "{prefix}{database}/".format(
                prefix=self.config.get("s3_key_prefix", ""),
                database=self.config.get("athena_database", "")
            )
            target_key = utils.get_target_key(
                self.stream_name,
                object_format,
                prefix=s3_prefix,
                timestamp=now,
                # naming_convention=self.config.get("naming_convention"),
            )
            if not (filename, target_key) in filenames:
                filenames.append((filename, target_key))

            file_is_empty = (not os.path.isfile(filename)) or os.stat(
                filename
            ).st_size == 0

            if self.config.get("flatten_records"):
                flattened_record = utils.flatten_record(record)
            else:
                flattened_record = record

            if object_format == 'csv':
                formats.write_csv(
                    filename = filename,
                    record = flattened_record,
                    header = headers,
                    delimiter = delimiter,
                    quotechar = quotechar
                )
            elif object_format == 'jsonl':
                formats.write_jsonl(
                    filename = filename,
                    record = flattened_record
                )
            else:
                self.logger.warn(f"Unrecognized format: '{object_format}'")

        # Create schemas in Athena
        self.logger.info("headers: {}".format(headers))
        data_location = "s3://{s3_bucket}/{key_prefix}{database}/{stream}/".format(
            s3_bucket=self.config.get("s3_bucket"),
            key_prefix=self.config.get("s3_key_prefix", ""),
            database=self.config.get("athena_database",""),
            stream=self.stream_name,
        )  # TODO: double check this
        if object_format == 'csv':
            ddl = athena.generate_create_table_ddl(
                self.stream_name,
                self.schema,
                headers=headers,
                database=self.config.get("athena_database"),
                data_location=data_location,
                row_format="org.apache.hadoop.hive.serde2.OpenCSVSerde",
            )
        elif object_format == 'jsonl':
            ddl = athena.generate_create_table_ddl(
                self.stream_name,
                self.schema,
                headers=headers,
                database=self.config.get("athena_database"),
                data_location=data_location,
                skip_header=False,
                row_format="org.openx.data.jsonserde.JsonSerDe",
                serdeproperties="'ignore.malformed.json'='true', 'case.insensitive'='false'"
            )
        else:
            self.logger.warn(f"Unrecognized format: '{object_format}'")
        self.logger.info(ddl)
        self.logger.info(data_location)
        athena.execute_sql(ddl, self.athena_client)

        # Upload created files to S3
        for filename, target_key in filenames:
            compressed_file = None
            if (
                self.config.get("compression") is None
                or self.config["compression"].lower() == "none"
            ):
                pass  # no compression
            else:
                if self.config["compression"] == "gzip":
                    compressed_file = f"{filename}.gz"
                    target_key = target_key + ".gz"
                    with open(filename, "rb") as f_in:
                        with gzip.open(compressed_file, "wb") as f_out:
                            self.logger.info(f"Compressing file as '{compressed_file}'")
                            shutil.copyfileobj(f_in, f_out)
                else:
                    raise NotImplementedError(
                        "Compression type '{}' is not supported. "
                        "Expected: 'none' or 'gzip'".format(self.config["compression"])
                    )
            s3.upload_file(
                compressed_file or filename,
                self.s3_client,
                self.config.get("s3_bucket"),
                target_key,
                encryption_type=self.config.get("encryption_type"),
                encryption_key=self.config.get("encryption_key"),
            )

            # Remove the local file(s)
            os.remove(filename)
            if compressed_file:
                os.remove(compressed_file)

        return state
