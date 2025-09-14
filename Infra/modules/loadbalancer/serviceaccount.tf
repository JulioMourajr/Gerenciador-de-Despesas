resource "kubernetes_service_account" "loadbalancerserviceaccount" {
  metadata {
    name      = "aws-load-balancer-controller"
    namespace = "kube-system"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.load_balancer_role.arn
    }
  }
}