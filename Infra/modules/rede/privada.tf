resource "aws_subnet" "eks_subnet_privada_a" {
  vpc_id            = aws_vpc.python-vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 3)
  availability_zone = "${data.aws_region.current.region}a"

  tags = {
    Name                              = var.privada_subnet_a_name
    "kubernetes.io/role/internal-elb" = 1
  }
}

resource "aws_subnet" "eks_subnet_privada_b" {
  vpc_id            = aws_vpc.python-vpc.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 4)
  availability_zone = "${data.aws_region.current.region}b"

  tags = {
    Name                              = var.privada_subnet_b_name
    "kubernetes.io/role/internal-elb" = 1
  }
}

resource "aws_route_table_association" "eks_private_route_table_a" {
  subnet_id      = aws_subnet.eks_subnet_privada_a.id
  route_table_id = aws_route_table.eks_private_route_table_a.id
}

resource "aws_route_table_association" "eks_private_route_table_b" {
  subnet_id      = aws_subnet.eks_subnet_privada_b.id
  route_table_id = aws_route_table.eks_private_route_table_b.id
}