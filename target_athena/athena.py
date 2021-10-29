import os
import singer
from logging import Logger
from pyathena import connect


def create_client(config, logger: Logger):
    """Generates an athena client object

    Args:
        config ([type]): [description]
        logger (Logger): [description]

    Returns:
        cursor: athena client object
    """

    logger.info("Attempting to create Athena session")

    # Get the required parameters from config file and/or environment variables
    aws_access_key_id = config.get("aws_access_key_id") or os.environ.get(
        "AWS_ACCESS_KEY_ID"
    )
    aws_secret_access_key = config.get("aws_secret_access_key") or os.environ.get(
        "AWS_SECRET_ACCESS_KEY"
    )
    aws_session_token = config.get("aws_session_token") or os.environ.get(
        "AWS_SESSION_TOKEN"
    )
    aws_profile = config.get("aws_profile") or os.environ.get("AWS_PROFILE")
    aws_region = config.get("aws_region") or os.environ.get("AWS_REGION")
    s3_staging_dir = config.get("s3_staging_dir") or os.environ.get("S3_STAGING_DIR")
    logger.info(f"Using Athena region {aws_region}")

    # AWS credentials based authentication
    if aws_access_key_id and aws_secret_access_key:
        cursor = connect(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region,
            s3_staging_dir=s3_staging_dir,
        ).cursor()

    # AWS Profile based authentication
    else:
        cursor = connect(
            profile_name=aws_profile,
            region_name=aws_region,
            s3_staging_dir=s3_staging_dir,
        ).cursor()
    return cursor

def execute_sql(sql, athena_client):
    """Run sql expression using athena client

    Args:
        sql (string): a valid sql statement string
        athena_client ([type]): [description]
    """
    athena_client.execute(sql)

def table_exists(athena_client, database, table_name):
    """Determine if a table already exists in athena.

    Args:
        athena_client ([type]): [description]
        database ([type]): [description]
        table_name ([type]): [description]

    Returns:
        bool: true/false
    """
    athena_client.execute("SHOW TABLES IN {database} '{table_name}';")
    if not athena_client.fetchall():
        return False
    else:
        return True

# This function is borrowed direclty from https://github.com/datadudes/json2hive/blob/master/json2hive/generators.py
def generate_column_definitions(schema, level=0):
    """Generates stringified column definitions for interpolation in the Hive table creation
    by recursively traversing a nested schema dictionary and inferring type according to 
    supported Hive types.

    Args:
        schema (dict): Schema dictionary
        level (int, optional): [description]. Defaults to 0.

    Returns:
        string: a stringified listi of column/type pairs.
    """
    keywords = ["timestamp", "date", "datetime"]
    tab = "  "
    type_separator = " " if level == 0 else ": "
    field_separator = ",\n" if level == 0 else ",\n"
    field_definitions = []
    new_level = level + 1
    indentation = new_level * tab
    for name, attributes in schema.items():
        cleaned_name = "`{}`".format(name)  # if name.lower() in keywords else name
        if attributes["type"] == "object":
            field_definitions.append(
                "{indentation}{name}{separator}STRUCT<\n{definitions}\n{indentation}>".format(
                    indentation=indentation,
                    name=cleaned_name,
                    separator=type_separator,
                    definitions=generate_column_definitions(
                        attributes["properties"], new_level
                    ),
                )
            )
        elif attributes["type"] == "array":
            extra_indentation = (new_level + 1) * tab
            if attributes["items"]["type"] == "object":
                closing_bracket = "\n" + indentation + ">"
                array_type = "STRUCT<\n{definitions}\n{indentation}>".format(
                    indentation=extra_indentation,
                    definitions=generate_column_definitions(
                        attributes["items"]["properties"], new_level + 1
                    ),
                )
            else:
                closing_bracket = ">"
                array_type = attributes["items"]["type"].upper()
            field_definitions.append(
                "{indentation}{name}{separator}ARRAY<{definitions}{closing_bracket}".format(
                    indentation=indentation,
                    name=cleaned_name,
                    separator=type_separator,
                    definitions=array_type,
                    closing_bracket=closing_bracket,
                )
            )
        elif isinstance(attributes["type"], list):
            types = [_ for _ in attributes["type"] if _ != "null"]
            field_definitions.append(
                "{indentation}{name}{separator}{type}".format(
                    indentation=indentation,
                    name=cleaned_name,
                    separator=type_separator,
                    type="STRING"
                    # type=types[0].upper()
                )
            )
        else:
            field_definitions.append(
                "{indentation}{name}{separator}{type}".format(
                    indentation=indentation,
                    name=cleaned_name,
                    separator=type_separator,
                    # type=attributes['type'].upper()
                    type="STRING",
                )
            )
    return field_separator.join(field_definitions)

def generate_create_database_ddl(
    database: str="default"
)-> None:
    return f"CREATE DATABASE IF NOT EXISTS {database};"

# This function is borrowed direclty from https://github.com/datadudes/json2hive/blob/master/json2hive/generators.py
def generate_create_table_ddl(
    table,
    schema,
    headers=None,
    data_location="",
    database="default",
    external=True,
    row_format="org.apache.hadoop.hive.serde2.OpenCSVSerde",
    serdeproperties = "'case.insensitive'='true'",
    skip_header = True,
):
    """Generate DDL for Hive table creation.

    Args:
        table ([type]): [description]
        schema ([type]): [description]
        headers ([type], optional): [description]. Defaults to None.
        data_location (str, optional): [description]. Defaults to "".
        database (str, optional): [description]. Defaults to "default".
        external (bool, optional): [description]. Defaults to True.
        row_format (str, optional): [description]. Defaults to "org.apache.hadoop.hive.serde2.OpenCSVSerde".
        serdeproperties (str, optional): [description]
        skip_header (bool, optional): [description]. Defaults to True.
    """

    if not headers:
        field_definitions = generate_column_definitions(schema["properties"])
    else:
        field_definitions = ",\n".join(["  `{}` STRING".format(_) for _ in headers])
    external_marker = "EXTERNAL " if external else ""
    row_format = "ROW FORMAT SERDE '{serde}'".format(serde=row_format) if row_format else ""
    stored = "\nSTORED AS TEXTFILE"
    serdeproperties = "\nWITH SERDEPROPERTIES ({})".format(serdeproperties) if serdeproperties else ""
    location = "\nLOCATION '{}'".format(data_location) if external else ""
    tblproperties = '\nTBLPROPERTIES ("skip.header.line.count" = "1")' if skip_header else ""
    statement = """CREATE {external_marker}TABLE IF NOT EXISTS {database}.{table} (
{field_definitions}
)
{row_format}{serdeproperties}{stored}{location}{tblproperties};""".format(
        external_marker=external_marker,
        database=database,
        table=table,
        field_definitions=field_definitions,
        row_format=row_format,
        serdeproperties=serdeproperties,
        stored=stored,
        location=location,
        tblproperties=tblproperties,
    )
    return statement

def create_or_replace_table(
    client,
    table,
    schema,
    headers=None,
    data_location="",
    database="default",
    external=True,
    row_format="org.apache.hadoop.hive.serde2.OpenCSVSerde",
    skip_header = True,
):
    if table_exists(athena_client=client, database=database, table_name=table):
        # alter table prefix
        alter_table = "ALTER TABLE {database}.{table} ".format(database, table)

        # update row_format
        # NOTE: this does not seem to be supported in Athena
        # execute_sql(ddl, client)

        # update columns
        if not headers:
            field_definitions = generate_column_definitions(schema["properties"])
        else:
            field_definitions = ", ".join(["`{}` STRING".format(_) for _ in headers])        
        ddl = alter_table + "REPLACE COLUMNS (field_definitions}".format(field_definitions)
        execute_sql(ddl, client)

        # update location
        ddl = alter_table + "SET LOCATION '{data_location}'".format(data_location)
        execute_sql(ddl, client)

        # skip_header
        ddl = alter_table + "SET TBLPROPERTIES ('skip.header.line.count'='{skip}');".format(skip=int(skip_header))
        execute_sql(ddl, client)        
    
    else:
        ddl = generate_create_table_ddl(
            table=table,
            schema=schema,
            headers=headers,
            database=database,
            data_location=data_location,
            skip_header=skip_header,
            row_format=row_format,
        )
        execute_sql(ddl, client)