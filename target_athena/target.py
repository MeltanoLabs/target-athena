"""Athena target class."""

from singer_sdk.target_base import Target
from singer_sdk import typing as th

from target_athena.sinks import (
    AthenaSink,
)


class TargetAthena(Target):
    """Sample target for Athena."""

    name = "target-athena"
    config_jsonschema = th.PropertiesList(
        th.Property("s3_bucket", th.StringType, required=True),
        th.Property("athena_database", th.StringType, required=True),
        th.Property("aws_region", th.StringType, required=True),
        th.Property("aws_access_key_id", th.StringType),
        th.Property("aws_secret_access_key", th.StringType),
        th.Property("aws_session_token", th.StringType),
        th.Property("aws_profile", th.StringType),
        th.Property("s3_key_prefix", th.StringType),
        th.Property("naming_convention", th.StringType),
        th.Property("object_format", th.StringType, default="jsonl"),
        th.Property("compression", th.StringType, default="gzip"),
        th.Property("encryption_type", th.StringType),
        th.Property("encryption_key", th.StringType),
        th.Property("add_record_metadata", th.BooleanType, default=False),
        th.Property("flatten_records", th.BooleanType, default=False),
        th.Property("delimiter", th.StringType, default=","),
        th.Property("quotechar", th.StringType, default='"'),
        th.Property("temp_dir", th.StringType),
        th.Property("stream_maps", th.ObjectType()),
        th.Property("stream_map_config", th.ObjectType()),
        th.Property("athena_workgroup", th.StringType, default="primary"),
        th.Property(
            "partition_config",
            th.ArrayType(
                th.ObjectType(
                    th.Property("stream_name", th.StringType, required=True),
                    th.Property("partition_key", th.StringType, required=True),
                )
            ),
            description="Configuration for partitioning data in S3. Each object should specify "
                      "the stream name and the key to use for partitioning."
        ),
    ).to_dict()
    default_sink_class = AthenaSink


cli = TargetAthena.cli

if __name__ == "__main__":
   TargetAthena.cli()