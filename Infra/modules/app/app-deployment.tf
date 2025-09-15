resource "kubernetes_deployment_v1" "aplicacao-deployment" {
  metadata {
    name      = "${var.app_name}-deployment"
    namespace = kubernetes_namespace.aplicacao.metadata[0].name
    labels = {
      app = var.app_name
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = var.app_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.app_name
        }
      }

      spec {
        container {
          name  = "${var.app_name}-container"
          image = var.app_image

          port {
            container_port = 8501
          }

          resources {
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
            requests = {
              cpu    = "250m"
              memory = "256Mi"
            }
          }

          env {
            name  = "STREAMLIT_SERVER_PORT"
            value = "8501"
          }

          env {
            name  = "STREAMLIT_SERVER_ADDRESS"
            value = "0.0.0.0"
          }
        }
      }
    }
  }
}