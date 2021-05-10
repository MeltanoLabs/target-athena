"""Athena tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers

from target_athena.streams import (
    AthenaStream,
)


class TapAthena(Tap):
    """Athena tap class."""
    name = "tap-athena"

    config_jsonschema = th.PropertiesList(
        th.Property("aws_region", th.StringType, required=True),
        th.Property("aws_access_key_id", th.StringType),
        th.Property("aws_secret_access_key", th.StringType),
        th.Property("aws_session_token", th.StringType),
        th.Property("aws_profile", th.StringType),
        th.Property("athena_database", th.StringType, required=True),
        th.Property("temp_dir", th.StringType),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


# CLI Execution:

cli = TapAthena.cli
