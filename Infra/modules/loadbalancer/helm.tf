resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = "1.13.3"
  namespace  = "kube-system"

  # Add force_update and cleanup options
  force_update    = false
  cleanup_on_fail = true
  atomic          = true
  wait            = true
  wait_for_jobs   = true
  timeout         = 500 # Increased timeout

  values = [
    yamlencode({
      clusterName = var.eks_cluster_name
      serviceAccount = {
        create = false
        name   = "aws-load-balancer-controller"
      }
      vpcId  = data.aws_eks_cluster.cluster.vpc_config[0].vpc_id
      region = data.aws_region.current.id
    })
  ]

  depends_on = [kubernetes_service_account.loadbalancerserviceaccount]
}