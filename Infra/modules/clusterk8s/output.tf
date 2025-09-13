output "eks_vpc_config" {
  value = aws_eks_cluster.eks_cluster.vpc_config
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.eks_cluster.endpoint
}

output "eks_cluster_name" {
  value = aws_eks_cluster.eks_cluster.id
}

output "oidc" {
  value = data.tls_certificate.certificado.certificates[*].sha1_fingerprint
}

output "oidc_id" {
  value = aws_eks_cluster.eks_cluster.identity[0].oidc[0].issuer
}

output "eks_cluster_ca_cert" {
  value = aws_eks_cluster.eks_cluster.certificate_authority[0].data
}