resource "aws_eks_cluster" "eks_cluster" {
  name     = "eks-cluster"
  role_arn = aws_iam_role.eks_cluster_role.arn

  vpc_config {
    subnet_ids = [
      var.publica_subnet_a_id,
      var.publica_subnet_b_id
    ]
    endpoint_private_access = true
    endpoint_public_access  = true
  }
  tags = {
    Name = "eks-cluster"
  }
  depends_on = [aws_iam_role_policy_attachment.eks_cluster_policy_attachment]
}