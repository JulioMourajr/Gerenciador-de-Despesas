resource "aws_iam_policy" "load_balancer_policy" {
  name   = "eks_load_balancer_policy"
  policy = file("${path.module}/iam_policy.json")
  tags = {
    Name = "eks_load_balancer_policy"
  }
}