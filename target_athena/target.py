"""Athena target class."""

from singer_sdk.target_base import Target
from singer_sdk import typing as th

from target_athena.sinks import (
    AthenaSink,
)

from tap_athena.tap import TapAthena

class TargetAthena(Target):
    """Sample target for Athena."""

    name = "target-athena"
    config_jsonschema = th.PropertiesList(
        th.Property("aws_region", th.StringType, required=True),
        th.Property("aws_access_key_id", th.StringType),
        th.Property("aws_secret_access_key", th.StringType),
        th.Property("aws_session_token", th.StringType),
        th.Property("aws_profile", th.StringType),
        th.Property("athena_database", th.StringType, required=True),
        th.Property("s3_key_prefix", th.StringType),
        th.Property("s3_bucket", th.StringType, required=True),
        th.Property("naming_convention", th.StringType),
        th.Property("compression", th.StringType, default='gzip'),
        th.Property("encryption_type", th.StringType),
        th.Property("encryption_key", th.StringType),
        th.Property("add_metadata_columns", th.BooleanType, default=False),
        th.Property("delimiter", th.StringType, default=","),
        th.Property("quotechar", th.StringType, default='"'),
        th.Property("temp_dir", th.StringType),
    ).to_dict()
    default_sink_class = AthenaSink

    @property
    def tap(self):
        def dict_subset(dict, keys) -> dict:
            return {
                k: v
                for k, v in dict.items()
                if k in keys
            }

        return TapAthena(
            config=dict_subset(
                self.config,
                keys=TapAthena.config_jsonschema.keys(),
            )
        )

cli = TargetAthena.cli
