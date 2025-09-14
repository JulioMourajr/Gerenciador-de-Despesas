resource "aws_eks_node_group" "eks_nodegroup" {
  cluster_name    = var.cluster_name
  node_group_name = "eks-managed-node-group-${random_string.suffix.result}" # Add random suffix
  node_role_arn   = aws_iam_role.eks_nodegroup_role.arn
  subnet_ids = [
    var.subnet_private1a,
    var.subnet_private1b
  ]

  scaling_config {
    desired_size = 6 # Reduced size
    max_size     = 8
    min_size     = 4
  }

  instance_types = ["t3.small"]
  disk_size      = 20

  # Add lifecycle policy
  lifecycle {
    create_before_destroy = true
  }

  # ...existing depends_on and tags...
}

# Add random string resource
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}