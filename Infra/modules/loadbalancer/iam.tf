resource "aws_iam_role" "load_balancer_role" {
  name               = "eks_load_balancer_role"
  assume_role_policy = <<EOF
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Federated": "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/oidc.eks.${data.aws_region.current.id}.amazonaws.com/id/${local.oidc_provider}"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
          "StringEquals": {
            "oidc.eks.${data.aws_region.current.id}.amazonaws.com/id/${local.oidc_provider}:aud": "sts.amazonaws.com",
            "oidc.eks.${data.aws_region.current.id}.amazonaws.com/id/${local.oidc_provider}:sub": "system:serviceaccount:kube-system:aws-load-balancer-controller"
          }
        }
      }
    ]
  }
  EOF

  tags = {
    Name = "eks_load_balancer_role"
  }
}

resource "aws_iam_role_policy_attachment" "load_balancer_policy_attachment" {
  policy_arn = aws_iam_policy.load_balancer_policy.arn
  role       = aws_iam_role.load_balancer_role.name
}