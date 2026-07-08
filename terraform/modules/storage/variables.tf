variable "name_prefix" {
  description = "Prefix applied to bucket and repository names."
  type        = string
}

variable "tags" {
  description = "Tags applied to all storage resources."
  type        = map(string)
  default     = {}
}
