resource "kubernetes_ingress" "aplicacao-ingress" {
  metadata {
    name      = "${var.app_name}-ingress"
    namespace = kubernetes_namespace.aplicacao.metadata[0].name

    annotations = {
      "kubernetes.io/ingress.class"                  = "alb"
      "alb.ingress.kubernetes.io/scheme"             = "internet-facing"
      "alb.ingress.kubernetes.io/target-type"        = "ip"
      "alb.ingress.kubernetes.io/listen-ports"       = "[{\"HTTP\": 80}]"
      "alb.ingress.kubernetes.io/load-balancer-name" = "${var.app_name}-alb"

      # Health check configurado para Streamlit
      "alb.ingress.kubernetes.io/healthcheck-path"             = "/"
      "alb.ingress.kubernetes.io/healthcheck-port"             = "8501"
      "alb.ingress.kubernetes.io/healthcheck-interval-seconds" = "30"
      "alb.ingress.kubernetes.io/healthcheck-timeout-seconds"  = "5"
      "alb.ingress.kubernetes.io/healthy-threshold-count"      = "2"
      "alb.ingress.kubernetes.io/unhealthy-threshold-count"    = "3"
    }
  }

  spec {
    rule {
      http {
        path {
          path = "/"

          backend {
            service_name = kubernetes_service.aplicacao-service.metadata[0].name
            service_port = 80
          }
        }
      }
    }
  }
}