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

variable "publica_subnet_a_name" {
  description = "The name of the public subnet A"
  type        = string
  default     = "publica-subnet-a"
}

variable "publica_subnet_b_name" {
  description = "The name of the public subnet B"
  type        = string
  default     = "publica-subnet-b"
}

variable "privada_subnet_a_name" {
  description = "The name of the private subnet A"
  type        = string
  default     = "privada-subnet-a"
}

variable "privada_subnet_b_name" {
  description = "The name of the private subnet B"
  type        = string
  default     = "privada-subnet-b"
}