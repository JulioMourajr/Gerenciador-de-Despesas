locals {
  oidc_provider = split("/", var.eks_cluster_oidc_id)[4]
}