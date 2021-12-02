# target-athena

[![PyPI version](https://badge.fury.io/py/target-athena.svg)](https://badge.fury.io/py/target-athena)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/target-athena.svg)](https://pypi.org/project/target-athena/)
[![License: Apache2](https://img.shields.io/badge/License-Apache2-yellow.svg)](https://opensource.org/licenses/Apache-2.0)

_Note: This target is derived from https://github.com/transferwise/pipelinewise-target-s3-csv_.  Some of the documentation below has not been completely updated yet.

[Singer](https://www.singer.io/) target that uploads loads data to AWS Athena in CSV format
following the [Singer spec](https://github.com/singer-io/getting-started/blob/master/docs/SPEC.md).

## How to use it

The recommended method of running this target is to use it from [PipelineWise](https://transferwise.github.io/pipelinewise). When running it from PipelineWise you don't need to configure this tap with JSON files and most of things are automated. Please check the related documentation at [Target S3 CSV](https://transferwise.github.io/pipelinewise/connectors/targets/s3_csv.html)

If you want to run this [Singer Target](https://singer.io) independently please read further.

## Install

First, make sure Python 3 is installed on your system or follow these
installation instructions for [Mac](http://docs.python-guide.org/en/latest/starting/install3/osx/) or
[Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-python-3-and-set-up-a-local-programming-environment-on-ubuntu-16-04).

It's recommended to use a virtualenv:

```bash
  python3 -m venv venv
  pip install git+https://github.com/MeltanoLabs/target-athena.git
```

or

```bash
  python3 -m venv venv
  . venv/bin/activate
  pip install --upgrade pip
  pip install .
```

### To run

Like any other target that's following the singer specificiation:

`some-singer-tap | target-athena --config [config.json]`

It's reading incoming messages from STDIN and using the properites in `config.json` to upload data into Postgres.

**Note**: To avoid version conflicts run `tap` and `targets` in separate virtual environments.

### Configuration settings

Running the the target connector requires a `config.json` file. An example with the minimal settings:

   ```json
   {
     "s3_bucket": "my_bucket",
     "athena_database": "my_database"
   }
   ```

### Profile based authentication

Profile based authentication used by default using the `default` profile. To use another profile set `aws_profile` parameter in `config.json` or set the `AWS_PROFILE` environment variable.

### Non-Profile based authentication

For non-profile based authentication set `aws_access_key_id` , `aws_secret_access_key` and optionally the `aws_session_token` parameter in the `config.json`. Alternatively you can define them out of `config.json` by setting `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_SESSION_TOKEN` environment variables.


Full list of options in `config.json`:

| Property                            | Type    | Required?  | Description                                                   |
|-------------------------------------|---------|------------|---------------------------------------------------------------|
| aws_access_key_id                   | String  | No         | S3 Access Key Id. If not provided, `AWS_ACCESS_KEY_ID` environment variable will be used. |
| aws_secret_access_key               | String  | No         | S3 Secret Access Key. If not provided, `AWS_SECRET_ACCESS_KEY` environment variable will be used. |
| aws_session_token                   | String  | No         | AWS Session token. If not provided, `AWS_SESSION_TOKEN` environment variable will be used. |
| aws_profile                         | String  | No         | AWS profile name for profile based authentication. If not provided, `AWS_PROFILE` environment variable will be used. |
| s3_bucket                           | String  | Yes        | S3 Bucket name                                                |
| s3_key_prefix                       | String  |            | A static prefix before the generated S3 key names. Using prefixes you can upload files into specific directories in the S3 bucket. Default(None)
| s3_staging_dir                       | String  | Yes         | S3 location to stage files. Example: s3://YOUR_S3_BUCKET/path/to/
| delimiter                           | String  |            | (Default: ',') A one-character string used to separate fields. |
| quotechar                           | String  |            | (Default: '"') A one-character string used to quote fields containing special characters, such as the delimiter or quotechar, or which contain new-line characters. |
| add_record_metadata                 | Boolean |            | (Default: False) Metadata columns add extra row level information about data ingestions, (i.e. when was the row read in source, when was inserted or deleted in snowflake etc.) Metadata columns are creating automatically by adding extra columns to the tables with a column prefix `_sdc_`. The column names are following the stitch naming conventions documented at https://www.stitchdata.com/docs/data-structure/integration-schemas#sdc-columns. Enabling metadata columns will flag the deleted rows by setting the `_sdc_deleted_at` metadata column. Without the `add_record_metadata` option the deleted rows from singer taps will not be recongisable in Snowflake. |
| encryption_type                     | String  | No         | (Default: 'none') The type of encryption to use. Current supported options are: 'none' and 'KMS'. |
| encryption_key                      | String  | No         | A reference to the encryption key to use for data encryption. For KMS encryption, this should be the name of the KMS encryption key ID (e.g. '1234abcd-1234-1234-1234-1234abcd1234'). This field is ignored if 'encryption_type' is none or blank. |
| compression                         | String  | No         | The type of compression to apply before uploading. Supported options are `none` (default) and `gzip`. For gzipped files, the file extension will automatically be changed to `.csv.gz` for all files. |
| naming_convention                   | String  | No         | (Default: None) Custom naming convention of the s3 key. Replaces tokens `date`, `stream`, and `timestamp` with the appropriate values. <br><br>Supports "folders" in s3 keys e.g. `folder/folder2/{stream}/export_date={date}/{timestamp}.csv`. <br><br>Honors the `s3_key_prefix`,  if set, by prepending the "filename". E.g. naming_convention = `folder1/my_file.csv` and s3_key_prefix = `prefix_` results in `folder1/prefix_my_file.csv` |
| temp_dir                            | String  |            | (Default: platform-dependent) Directory of temporary CSV files with RECORD messages. |

### To run tests:

1. Define environment variables that requires running the tests
```
  export TARGET_ATHENA_ACCESS_KEY_ID=<s3-access-key-id>
  export TARGET_ATHENA_SECRET_ACCESS_KEY=<s3-secret-access-key>
  export TARGET_ATHENA_BUCKET=<s3-bucket>
  export TARGET_ATHENA_KEY_PREFIX=<s3-key-prefix>
```

2. Install python test dependencies in a virtual env and run nose unit and integration tests
```
  python3 -m venv venv
  . venv/bin/activate
  pip install --upgrade pip
  pip install .[test]
```

3. To run unit tests:
```
  nosetests --where=tests/unit
```

4. To run integration tests:
```
  nosetests --where=tests/integration
```

### To run pylint:

1. Install python dependencies and run python linter
```
  python3 -m venv venv
  . venv/bin/activate
  pip install --upgrade pip
  pip install .
  pip install pylint
  pylint target_athena -d C,W,unexpected-keyword-arg,duplicate-code
```

## License

Apache License Version 2.0

See [LICENSE](LICENSE) to see the full text.
