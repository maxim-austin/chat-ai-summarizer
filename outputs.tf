#########################
#  outputs.tf
#########################

output "lambda_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.chat_summarizer_lambda.arn
}
