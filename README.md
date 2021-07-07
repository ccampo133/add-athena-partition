# add-athena-partition

Python script to manually add a partition to an Athena table based on today's date. 

Inspired by https://github.com/buzzsurfr/athena-add-partition

## Background 

Because some S3 data 
[is not partitioned in Hive format](https://docs.aws.amazon.com/athena/latest/ug/partitions.html#scenario-2-data-is-not-partitioned),
it is necessary to manually add Athena partitions by executing an `ALTER TABLE ... ADD PARTITION ...` statement. This 
repository contains a Python script to do that based on today's date (or a specified date), or add all existing 
partitions. Additionally, the script can be run as an AWS Lambda function, and can be triggered by a scheduled 
CloudWatch event.

## Usage

You can execute `add_athena_partition` from either the command line or as an AWS Lambda function. Both approaches are
detailed below.

### Command Line

Run using Python (3.7+)

```
$ python add_athena_partiton.py --help

usage: add_athena_partition.py [-h] --database DATABASE --table TABLE --location LOCATION --query-result-location QUERY_RESULT_LOCATION [--date DATE] [--load-all] [--log-level LOG_LEVEL]

Add a partition an Athena table.

optional arguments:
  -h, --help            show this help message and exit
  --database DATABASE   The Athena database name
  --table TABLE         The Athena table name
  --location LOCATION   The S3 location of the data (S3 URI)
  --query-result-location QUERY_RESULT_LOCATION
                        The S3 location to store Athena query results (S3 URI)
  --date DATE           The date of the partition (YYYY-MM-DD, default: today)
  --load-all            Load all available partitions
  --log-level LOG_LEVEL
                        The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

### AWS Lambda

When executing as an AWS Lambda function, `add_athena_partition` expects all arguments to be passed as an event of the
following JSON format. The minimum required arguments are:

```json
{
  "database": "string",
  "table": "string",
  "location": "string",
  "query_result_location": "string"
}
```

Both the `location` and `query_result_location` attributes _must be_ S3 URIs, e.g. `s3://{bucket_name}/{prefix}/...`.

This will assume `date` as the date the Lambda is executed. If you want to pass a specific date, provide the `date`
attribute in the event JSON in the `YYYY-MM-DD` string format.

Additionally, the `log_level` and `load_all` string arguments can be passed, following the same format outlined in the 
usage above.

Within Lambda itself, the handler method should be configured as `add_athena_partition.lambda_handler`.

Assuming the function is created and exists in Lambda already (for example, called `add_athena_partition`), deployment
is simple using the command line:

```
$ zip add_athena_partition.zip add_athena_partition.py
$ aws lambda update-function-code --function-name add_athena_partition --zip-file fileb://add_athena_partition.zip
```

This project includes functional [Terraform](https://www.terraform.io/) code to deploy this as a Lambda function to an
AWS environment. See [`terraform`](terraform) for more details.

## Development

Requires: Python 3.7+

Create a [virtualenv](https://docs.python.org/3/library/venv.html):

    $ python3 -m venv venv  
    # ...or just 'python', assuming that points to a >=Python 3.7 installation

Then activate it:

    $ source venv/bin/activate

Next, install the requirements:

    $ pip install -r requirements.txt

## CI/CD

This project is build with GitHub Actions. See [`.github/workflows`](.github/workflows) for specifics. 
