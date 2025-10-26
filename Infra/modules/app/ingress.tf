resource "kubernetes_ingress_v1" "aplicacao-ingress" {
  metadata {
    name      = "${var.app_name}-ingress"
    namespace = var.namespace
    annotations = {
      "kubernetes.io/ingress.class"                  = "alb"
      "alb.ingress.kubernetes.io/scheme"             = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"        = "ip"
      "alb.ingress.kubernetes.io/listen-ports"       = "[{\"HTTP\": 80}]"
      "alb.ingress.kubernetes.io/healthcheck-path"   = "/"
      "alb.ingress.kubernetes.io/healthcheck-port"   = "80"
      "alb.ingress.kubernetes.io/load-balancer-name" = "${var.app_name}-alb"
    }
  }

  spec {
    rule {
      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = "${var.app_name}-service"
              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }
}