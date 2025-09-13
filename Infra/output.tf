output "vpc_id" {
  value = module.rede_eks.aws_vpc_id
}

output "subnet_publica_a_id" {
  value = module.rede_eks.aws_subnet_publica_a_id
}

output "subnet_publica_b_id" {
  value = module.rede_eks.aws_subnet_publica_b_id
}

output "subnet_privada_a_id" {
  value = module.rede_eks.aws_subnet_privada_a_id
}

output "subnet_privada_b_id" {
  value = module.rede_eks.aws_subnet_privada_b_id
}