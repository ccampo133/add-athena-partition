import argparse
import datetime
import logging

import boto3

athena = boto3.client('athena')
s3 = boto3.client('s3')
s3_paginator = s3.get_paginator('list_objects')

logger = logging.getLogger()


# Adapted from "athena-add-partition" (https://github.com/buzzsurfr/athena-add-partition)
def add_athena_partition(database, table, location, query_result_location, date=None):
    """
    Add today's year/month/day partition to an Athena table

    See: https://docs.aws.amazon.com/athena/latest/ug/alter-table-add-partition.html

    :param database: The Athena database name
    :param table: The Athena table name
    :param location: The S3 location of the data (S3 URI)
    :param query_result_location: The S3 location to store query results (S3 URI)
    :param date: The date of the partition (YYYY-MM-DD, default: today)
    """
    dt = datetime.datetime.now() if not date else datetime.datetime.strptime(date, "%Y-%m-%d")

    year = dt.strftime('%Y')
    month = dt.strftime('%m')
    day = dt.strftime('%d')

    query_string = f"ALTER TABLE {table} " \
                   f"ADD PARTITION (year=\"{year}\",month=\"{month}\",day=\"{day}\") " \
                   f"LOCATION \"{location + year}/{month}/{day}/\""

    logger.info(f"Athena query_string: {query_string}")

    query_execution_context = {
        "Database": database
    }

    result_configuration = {
        "OutputLocation": query_result_location
    }

    # Create new partition in Athena table
    result = athena.start_query_execution(
        QueryString=query_string,
        QueryExecutionContext=query_execution_context,
        ResultConfiguration=result_configuration
    )

    logger.info(f"QueryExecutionId: {result['QueryExecutionId']}")


def add_all_partitions(database, table, location, query_result_location):
    bucket, path = split_s3_bucket_key(location)

    # This assumes that the ultimate "folder" in the S3 bucket is of the form YYYY/MM/DD.
    # If that is not the case, this will not work properly. ¯\_(ツ)_/¯
    def callback(prefix):
        date = prefix[-11:-1].replace("/", "-")
        add_athena_partition(
            database=database,
            table=table,
            location=location,
            query_result_location=query_result_location,
            date=date
        )

    recursive_list_folders(
        bucket=bucket,
        prefix=path,
        callback=callback
    )


def parse_args():
    parser = argparse.ArgumentParser(description='Add a partition an Athena table.')
    parser.add_argument('--database', action='store', required=True, help='The Athena database name')
    parser.add_argument('--table', action='store', required=True, help='The Athena table name')
    parser.add_argument('--location', action='store', required=True, help='The S3 location of the data (S3 URI)')
    parser.add_argument('--query-result-location', action='store', required=True,
                        help='The S3 location to store Athena query results (S3 URI)')
    parser.add_argument('--date', action='store', required=False,
                        help='The date of the partition (YYYY-MM-DD, default: today)', default=None)
    parser.add_argument('--load-all', action='store_true', required=False, default=False,
                        help='Load all available partitions')
    parser.add_argument('--log-level', action='store', required=False, default="INFO",
                        help='The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    return parser.parse_args()


def find_bucket_key(s3_path):
    s3_components = s3_path.split('/')
    bucket = s3_components[0]
    s3_key = ''
    if len(s3_components) > 1:
        s3_key = '/'.join(s3_components[1:])
    return bucket, s3_key


def split_s3_bucket_key(s3_path):
    if s3_path.startswith('s3://'):
        s3_path = s3_path[5:]
    return find_bucket_key(s3_path)


def recursive_list_folders(bucket, prefix, callback, max_depth=10):
    if max_depth <= 0:
        raise RuntimeError("Max recursion depth exceeded")

    result = s3_paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/")
    for common_prefix in result.search('CommonPrefixes'):
        if not common_prefix:
            callback(prefix)
            break
        sub_prefix = common_prefix.get("Prefix")
        recursive_list_folders(bucket, sub_prefix, callback, max_depth - 1)


def main(database, table, location, query_result_location, load_all, date):
    if load_all:
        logger.info("Loading all available partitions")
        add_all_partitions(
            database=database,
            table=table,
            location=location,
            query_result_location=query_result_location,
        )
    else:
        logger.info("Loading single partition")
        add_athena_partition(
            database=database,
            table=table,
            location=location,
            query_result_location=query_result_location,
            date=date
        )


def lambda_handler(event, context):
    """
    Invoked by AWS Lambda. Args are expected to be passed as in the trigger event.

    See: https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html
    """
    if 'log_level' in event:
        logger.setLevel(event['log_level'].upper())
    else:
        logger.setLevel(logging.INFO)

    logger.info(f"Invoked by Lambda event: {event}")
    logger.info(f"Request ID: {context.aws_request_id}")
    logger.info(f"Log stream name: {context.log_stream_name}")
    logger.info(f"Log group name: {context.log_group_name}")
    logger.info(f"Memory limit (MB): {context.memory_limit_in_mb}")

    main(
        database=event['database'],
        table=event['table'],
        location=event['location'],
        query_result_location=event['query_result_location'],
        date=event['date'] if 'date' in event else None,
        load_all='load_all' in event and bool(event['load_all'])
    )


# Run from the command line
if __name__ == '__main__':
    args = parse_args()

    logger.setLevel(args.log_level.upper())

    main(
        database=args.database,
        table=args.table,
        location=args.location,
        query_result_location=args.query_result_location,
        load_all=args.load_all,
        date=args.date
    )
