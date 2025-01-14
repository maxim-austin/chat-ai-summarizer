#########################
#  main.tf
#########################

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.3.0"
}

terraform {
  backend "s3" {
    bucket = "chatsummarizer"
    key    = "chat-summarizer-lambda/terraform.tfstate"
    region = "us-west-2"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name               = "chat_summarizer_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Function with Python 3.12 runtime
resource "aws_lambda_function" "chat_summarizer_lambda" {
  function_name = "chat_summarizer_lambda"
  handler       = "main.lambda_handler"
  runtime       = "python3.12"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 500

  # We reference the zip file we build/commit via GitHub Actions
  filename = "${path.module}/package.zip"

  depends_on = [aws_iam_role_policy_attachment.lambda_basic_execution]
}

# EventBridge Rule for Daily Trigger
resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "chat-summarizer-daily-trigger"
  schedule_expression = "cron(0 4 * * ? *)"  # 4:00 AM UTC = 10 PM US Central
  description         = "Triggers the Lambda daily at 10 PM US Central"
}

# Allow EventBridge to invoke the Lambda
resource "aws_lambda_permission" "allow_event_bridge" {
  statement_id  = "AllowDailyEvent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chat_summarizer_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
}

# Attach the Lambda to EventBridge Rule
resource "aws_cloudwatch_event_target" "daily_trigger_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  arn       = aws_lambda_function.chat_summarizer_lambda.arn
}

