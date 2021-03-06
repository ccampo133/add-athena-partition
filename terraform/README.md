# Terraform

This directory contains the Terraform files necessary to create the `add_athena_partition` AWS Lambda function and its
supporting infrastructure (S3 bucket, CloudWatch events).

A Lambda function called `add_athena_partition` will be deployed with configurable CloudWatch Event Rule triggers, 
scheduled to run once every day by default (but configurable via Terraform variables).

If you are deploying this to multiple environments (e.g. dev, staging, production), it's recommended that each
environment has a corresponding `<environment>.tfvars` file which describes the configuration for that environment.

The Terraform state will be stored in an S3 in a bucket of your choice with the key `add_athena_partition.tfstate`.

Note that the Lambda function is created with a empty (dummy) zip file. The actual lambda code must be pushed 
separately, such as using the [AWS command line](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html).

Modifying this terraform to push build code is fairly trivial. Just replace `dummy.zip` with the code package and 
re-apply. Alternatively, you can [specify the deployment package via Amazon S3](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function#specifying-the-deployment-package).

Please feel free to make modifications to the Terraform code as you see fit.

## Requirements

* Terraform (version >= 0.12.6)
* AWS credentials with access to create Lambda functions and CloudWatch events

## Usage

The below example assumes that your AWS credentials are set as environment variables, or in a
[`credentials` file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) under the `default`
profile. You can optionally specify the profile if you wish as well. See
[Terraform's AWS provider docs](https://www.terraform.io/docs/providers/aws/index.html) for more details.

Additionally, we must init the [S3 backend](https://www.terraform.io/docs/backends/types/s3.html) to store the state
file before doing anything.

```
# Substitute the region and bucket as necessary
terraform init \
    -backend-config="region=us-east-1" \
    -backend-config="bucket=example-tfstate-bucket" \

# Always check the plan first!
terraform plan -var-file="dev.tfvars"

# Then apply...
terraform apply -var-file="dev.tfvars"

# ...and optionally teardown
terraform destroy -var-file="dev.tfvars"
```

See [`variables.tf`](./variables.tf) and [`outputs.tf`](outputs.tf) for information on inputs and outputs respectively.
