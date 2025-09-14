data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_eks_cluster" "cluster" {
  name = var.eks_cluster_name
}