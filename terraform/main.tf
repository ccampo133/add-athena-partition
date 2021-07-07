terraform {
  required_version = ">= 0.12.29"

  backend "s3" {
    key = "add_athena_partition.tfstate"
  }
}

provider "aws" {
  version = "~> 3.26"
  profile = var.profile
  region = var.region
}

resource "aws_cloudwatch_event_rule" "add_athena_partition_rule" {
  name = "partition_${var.athena_table_name}"
  description = "Triggers adding a partition to the Athena table '${var.athena_db_name}.${var.athena_table_name}'."
  schedule_expression = "rate(${var.rate})"
}

resource "aws_cloudwatch_event_target" "add_athena_partition_target" {
  rule = aws_cloudwatch_event_rule.add_athena_partition_rule.name
  target_id = aws_cloudwatch_event_rule.add_athena_partition_rule.name
  arn = aws_lambda_function.add_athena_partition.arn
  input = <<INPUT
{
  "database": "${var.athena_db_name}",
  "table": "${var.athena_table_name}",
  "location": "${var.s3_location}"
  "query_result_location": "${var.s3_query_result_location}"
}
INPUT
}

resource "aws_iam_role" "add_athena_partition_lambda_role" {
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })

  # These are provided by AWS
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/AmazonAthenaFullAccess",
    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  ]
}

resource "aws_lambda_function" "add_athena_partition" {
  function_name = "add_athena_partition"
  handler = "add_athena_partition.lambda_handler"
  role = aws_iam_role.add_athena_partition_lambda_role.arn
  runtime = "python3.7"
  memory_size = var.memory_size
  timeout = var.timeout

  # Terraform needs a file to bootstrap the Lambda function, so we just use a dummy
  filename = "dummy.zip"
}

resource "aws_lambda_permission" "allow_execution_cloudwatch_permission" {
  statement_id = "allow_execution_from_cloudwatch_${var.athena_db_name}_${var.athena_table_name}"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.add_athena_partition.function_name
  principal = "events.amazonaws.com"
  source_arn = aws_cloudwatch_event_rule.add_athena_partition_rule.arn
}
