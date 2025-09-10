variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "192.168.0.0/16"
}
variable "vpc_name" {
  description = "The name of the VPC"
  type        = string
  default     = "python-vpc"
}