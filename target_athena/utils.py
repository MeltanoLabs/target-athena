from datetime import datetime
import time
import singer
import json
import re
import collections
import inflection

from decimal import Decimal
from datetime import datetime

logger = singer.get_logger("target_athena")


def float_to_decimal(value):
    """Walk the given data structure and turn all instances of float into
    double."""
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, list):
        return [float_to_decimal(child) for child in value]
    if isinstance(value, dict):
        return {k: float_to_decimal(v) for k, v in value.items()}
    return value


# pylint: disable=unnecessary-comprehension
def flatten_key(k, parent_key, sep):
    """"""
    full_key = parent_key + [k]
    inflected_key = [n for n in full_key]
    reducer_index = 0
    while len(sep.join(inflected_key)) >= 255 and reducer_index < len(inflected_key):
        reduced_key = re.sub(
            r"[a-z]", "", inflection.camelize(inflected_key[reducer_index])
        )
        inflected_key[reducer_index] = (
            reduced_key if len(reduced_key) > 1 else inflected_key[reducer_index][0:3]
        ).lower()
        reducer_index += 1

    return sep.join(inflected_key)


def flatten_record(d, parent_key=[], sep="__"):
    """"""
    items = []
    for k in sorted(d.keys()):
        v = d[k]
        new_key = flatten_key(k, parent_key, sep)
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_record(v, parent_key + [k], sep=sep).items())
        else:
            items.append((new_key, json.dumps(v) if type(v) is list else v))
    return dict(items)


def get_target_key(stream_name, object_format, prefix="", timestamp=None, partition_key=None):
    """Creates and returns an S3 key for the message"""

    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    if not prefix.endswith("/"):
        prefix += "/"
    if not partition_key.endswith("/"):
        partition_key += "/"
    key = f"{prefix}{stream_name}/{partition_key}{timestamp}.{object_format}"

    return key 
