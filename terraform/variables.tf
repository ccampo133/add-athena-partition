# Required
variable "s3_location" {
  type = string

  # For ALB logs, this is usually something like:
  # s3://{bucket}/{prefix}/AWSLogs/${aws_account_id}/elasticloadbalancing/{aws_region}/
  description = "The S3 location of the data (S3 URI)"
}

variable "s3_query_result_location" {
  type = string

  # For Athena, this is usually something like:
  # s3://aws-athena-query-results-{aws_account_id}-{aws_region}/"
  description = "The S3 location to store Athena query results (S3 URI)"
}

variable "athena_db_name" {
  type = string
  description = "The Athena database name"
}

variable "athena_table_name" {
  type = string
  description = "The Athena table name"
}

# Optional
variable "profile" {
  type = string
  default = "default"
  description = "The AWS credentials profile"
}

variable "region" {
  type = string
  default = "us-east-1"
  description = "The AWS region"
}

variable "rate" {
  type = string
  default = "1 day"
}

variable "memory_size" {
  type = number
  default = 128
  description = "The allocated memory for the Lambda function, in MB"
}

variable "timeout" {
  type = number
  default = 300
  description = "The amount of time the Lambda function has to run, in seconds"
}
