variable "namespace" {
  description = "The namespace to deploy the application"
  type        = string
  default     = "aplicacao"
}

variable "app_name" {
  description = "The name of the application"
  type        = string
  default     = "aplicacao"
}

variable "app_image" {
  description = "The Docker image of the application"
  type        = string
  default     = "juliomourajr92/regressiva:1.5"
}