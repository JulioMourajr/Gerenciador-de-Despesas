module "rede" {
  source = "./modules/rede"
}

module "clusterk8s" {
  source              = "./modules/clusterk8s"
  publica_subnet_a_id = module.rede.aws_subnet_publica_a_id
  publica_subnet_b_id = module.rede.aws_subnet_publica_b_id
}

module "nodegroup" {
  source           = "./modules/nodegroup"
  cluster_name     = module.clusterk8s.eks_cluster_name
  subnet_private1a = module.rede.aws_subnet_privada_a_id
  subnet_private1b = module.rede.aws_subnet_privada_b_id
}