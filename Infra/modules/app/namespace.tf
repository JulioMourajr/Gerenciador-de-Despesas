resource "kubernetes_namespace" "aplicacao" {
  metadata {
    name = var.namespace

    labels = {
      name = var.namespace
      app  = "aplicacao"
    }
  }
}