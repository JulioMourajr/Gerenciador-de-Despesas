variable "cluster_name" {
  description = "The name of the EKS cluster"
  type        = string
}

variable "subnet_private1a" {
  description = "The ID of the private subnet 1a"
  type        = string
}

variable "subnet_private1b" {
  description = "The ID of the private subnet 1b"
  type        = string
}