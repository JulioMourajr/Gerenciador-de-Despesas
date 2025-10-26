resource "kubernetes_service" "aplicacao-service" {
  metadata {
    name      = "${var.app_name}-service"
    namespace = kubernetes_namespace.aplicacao.metadata[0].name
    labels = {
      app = var.app_name
    }
  }

  spec {
    selector = {
      app = kubernetes_deployment_v1.aplicacao-deployment.metadata[0].labels.app
    }

    port {
      name        = "http"
      port        = 80
      target_port = 80
    }
    type = "NodePort"
  }
}