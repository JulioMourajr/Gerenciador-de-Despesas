module "rede" {
  source = "./modules/rede"
}

module "clusterk8s" {
  source              = "./modules/clusterk8s"
  publica_subnet_a_id = module.rede.aws_subnet_publica_a_id
  publica_subnet_b_id = module.rede.aws_subnet_publica_b_id
}