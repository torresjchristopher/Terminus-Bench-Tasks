output "ecs_task_execution_role_arn" {
  description = "ARN of ECS task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

output "s3_replication_role_arn" {
  description = "ARN of S3 replication role"
  value       = aws_iam_role.s3_replication.arn
}
