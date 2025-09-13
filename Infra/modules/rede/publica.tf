resource "aws_subnet" "eks_subnet_publica_a" {
  vpc_id                  = aws_vpc.python-vpc.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 1)
  availability_zone       = "${data.aws_region.current.region}a"
  map_public_ip_on_launch = true

  tags = {
    Name                     = var.publica_subnet_a_name
    "kubernetes.io/role/elb" = 1
  }
}

resource "aws_subnet" "eks_subnet_publica_b" {
  vpc_id                  = aws_vpc.python-vpc.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 2)
  availability_zone       = "${data.aws_region.current.region}b"
  map_public_ip_on_launch = true

  tags = {
    Name                     = var.publica_subnet_b_name
    "kubernetes.io/role/elb" = 1
  }
}

resource "aws_route_table_association" "eks_public_route_table_a" {
  subnet_id      = aws_subnet.eks_subnet_publica_a.id
  route_table_id = aws_route_table.eks_public_route_table.id
}

resource "aws_route_table_association" "eks_public_route_table_b" {
  subnet_id      = aws_subnet.eks_subnet_publica_b.id
  route_table_id = aws_route_table.eks_public_route_table.id
}