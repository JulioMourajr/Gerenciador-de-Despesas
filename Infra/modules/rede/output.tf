output "aws_vpc_id" {
  value = aws_vpc.python-vpc.id
}

output "aws_subnet_publica_a_id" {
  value = aws_subnet.eks_subnet_publica_a.id
}

output "aws_subnet_publica_b_id" {
  value = aws_subnet.eks_subnet_publica_b.id
}

output "aws_subnet_privada_a_id" {
  value = aws_subnet.eks_subnet_privada_a.id
}

output "aws_subnet_privada_b_id" {
  value = aws_subnet.eks_subnet_privada_b.id
}

