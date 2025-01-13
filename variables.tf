#########################
#  variables.tf
#########################

variable "aws_region" {
  type        = string
  description = "AWS region where all resources will be deployed"
  default     = "us-west-2"
}

variable "aws_account_id" {
  type        = string
  description = "AWS Account ID (stored as a secret in GitHub)"
}
