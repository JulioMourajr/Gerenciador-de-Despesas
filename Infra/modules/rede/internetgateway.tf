resource "aws_internet_gateway" "eks_igw" {
  vpc_id = aws_vpc.python-vpc.id

  tags = {
    Name = "eks-internet-gateway"
  }
}

resource "aws_route_table" "eks_public_route_table" {
  vpc_id = aws_vpc.python-vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.eks_igw.id
  }

  tags = {
    Name = "eks-public-route-table"
  }
}