terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.38.0"
    }

    helm = {
      source  = "hashicorp/helm"
      version = "3.0.2"
    }
  }
  backend "s3" {
    bucket = "devopsarrocha-terraform-bucket2025"
    key    = "github/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "kubernetes" {
  host                   = module.clusterk8s.eks_cluster_endpoint
  cluster_ca_certificate = base64decode(module.clusterk8s.eks_cluster_ca_cert)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    args        = ["eks", "get-token", "--cluster-name", module.clusterk8s.eks_cluster_name]
    command     = "aws"
  }
}

provider "helm" {
  kubernetes = {
    host                   = module.clusterk8s.eks_cluster_endpoint
    cluster_ca_certificate = base64decode(module.clusterk8s.eks_cluster_ca_cert)
    exec = {
      api_version = "client.authentication.k8s.io/v1beta1"
      args        = ["eks", "get-token", "--cluster-name", module.clusterk8s.eks_cluster_name]
      command     = "aws"
    }
  }
}
