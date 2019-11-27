# See https://docs.aws.amazon.com/lambda/latest/dg/tutorial-scheduled-events-schedule-expressions.html
# for how to write schedule expressions
variable "ebs_snapshot_backups_schedule" {
  default = "cron(00 19 * * ? *)"
}

variable "ebs_snapshot_janitor_schedule" {
  default = "cron(05 19 * * ? *)"
}

variable "backup_tag" {
  description = "Set the tag that will be used to find instance for backup"
  default     = "Backup"
}

variable "retention" {
  description = "Set retention period"
  default     = "7d"
}

variable "backup_lambda_name" {
  description = "Set name for backup lambda func"
  default     = "schedule_ebs_snapshot_backups"
}

variable "retention_lambda_name" {
  description = "Set name for retention lambda func"
  default     = "ebs_snapshot_janitor"
}

variable "iam_role_name" {
  description = "Set name for iam role"
  default     = "lambda-backup-role"
}

variable "iam_role" {
  description = "Set predefined IAM role"
  default     = ""
}

variable "create_iam_role" {
  description = "Should the module create IAM role?"
  default     = true
}

