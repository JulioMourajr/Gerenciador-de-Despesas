resource "aws_eks_node_group" "example" {
  cluster_name    = var.cluster_name
  node_group_name = "eks-managed-node-group"
  node_role_arn   = aws_iam_role.eks_nodegroup_role.arn
  subnet_ids = [
    var.subnet_private1a,
    var.subnet_private1b
  ]

  scaling_config {
    desired_size = 8
    max_size     = 10
    min_size     = 6
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy_attachment,
    aws_iam_role_policy_attachment.eks_cni_policy_attachment,
    aws_iam_role_policy_attachment.eks_ecr_policy_attachment
  ]

  tags = {
    Name = "eks-managed-node-group"
  }
}
