resource "aws_eip" "eks_eip_1a" {
  tags = {
    Name = "eks-natgateway-eip-1a"
  }
}

resource "aws_eip" "eks_eip_1b" {
  tags = {
    Name = "eks-natgateway-eip-1b"
  }
}

resource "aws_nat_gateway" "eks_nat_gateway_a" {
  allocation_id = aws_eip.eks_eip_1a.id
  subnet_id     = aws_subnet.eks_subnet_publica_a.id

  tags = {
    Name = "eks-nat-gateway-a"
  }
}

resource "aws_nat_gateway" "eks_nat_gateway_b" {
  allocation_id = aws_eip.eks_eip_1b.id
  subnet_id     = aws_subnet.eks_subnet_publica_b.id

  tags = {
    Name = "eks-nat-gateway-b"
  }
}

resource "aws_route_table" "eks_private_route_table_a" {
  vpc_id = aws_vpc.python-vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.eks_nat_gateway_a.id
  }

  tags = {
    Name = "eks-private-route-table-a"
  }
}

resource "aws_route_table" "eks_private_route_table_b" {
  vpc_id = aws_vpc.python-vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.eks_nat_gateway_b.id
  }

  tags = {
    Name = "eks-private-route-table-b"
  }
}