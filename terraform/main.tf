provider "aws" {
  version = "~> 2.69.0"
  region  = var.region
}

terraform {
  required_version = ">= 0.12"
}

# get AWS account ID
data "aws_caller_identity" "current" {}

# VPC with a single public subnet
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "pico"
  cidr = "10.0.0.0/16"

  azs             = [ "${var.az}" ]
  public_subnets  = ["10.0.0.0/24"]

  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_security_group" "container" {
  name        = "picobrew-container"
  description = "Picobrew container"
  vpc_id      = module.vpc.vpc_id
}

# allow ingress to container on port 80 from specified CIDR blocks
resource "aws_security_group_rule" "container_in" {
  type                     = "ingress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  cidr_blocks              = var.cidr_access
  security_group_id        = aws_security_group.container.id
}

# allow container egress on all ports
resource "aws_security_group_rule" "container_out" {
  type                     = "egress"
  from_port                = 0
  to_port                  = 0
  protocol                 = -1
  cidr_blocks              = [ "0.0.0.0/0" ]
  security_group_id        = aws_security_group.container.id
}

resource "aws_security_group" "nfs_mount" {
  name        = "picobrew-nfs-mount"
  description = "Picobrew NFS mount"
  vpc_id      = module.vpc.vpc_id
}

# allow EFS mount egress on all ports
resource "aws_security_group_rule" "nfs_mount_out" {
  type                     = "egress"
  from_port                = 0
  to_port                  = 0
  protocol                 = -1
  cidr_blocks              = [ "0.0.0.0/0" ]
  security_group_id        = aws_security_group.nfs_mount.id
}

# allow ingress to EFS mount from picobrew container
resource "aws_security_group_rule" "nfs_mount_in" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 0
  protocol                 = -1
  source_security_group_id = aws_security_group.container.id
  security_group_id        = aws_security_group.nfs_mount.id
}

resource "aws_efs_file_system" "picobrew" {
  creation_token = "picobrew"
  encrypted      = true

  lifecycle_policy {
    transition_to_ia = "AFTER_7_DAYS"
  }
}

# allow access to EFS from all services
/*data "aws_iam_policy_document" "picobrew_efs_policy" {
  statement {
    actions = [ "elasticfilesystem:ClientMount",
                "elasticfilesystem:ClientWrite" ]
    effect  = "Allow"

    principals {
    #  identifiers = [ "ecs-tasks.amazonaws.com" ]
    #  type        = "Service"
    identifiers = [ "*" ]
      type        = "*"
    }
    
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"

      values = [ "true" ]
    }
  }
}

resource "aws_efs_file_system_policy" "picobrew_policy" {
  file_system_id = aws_efs_file_system.picobrew.id

  policy = data.aws_iam_policy_document.picobrew_efs_policy.json
}*/

resource "aws_efs_mount_target" "picobrew" {
  file_system_id  = aws_efs_file_system.picobrew.id
  subnet_id       = element(module.vpc.public_subnets, 0)
  security_groups = [ aws_security_group.nfs_mount.id ]
}

# create log group for container logs and set expiry to 1 day
resource "aws_cloudwatch_log_group" "picobrew" {
  name              = "picobrew"
  retention_in_days = "1"
}

data "aws_iam_policy_document" "picobrew_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    effect  = "Allow"

    principals {
      identifiers = ["ecs-tasks.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "picobrew" {
  name = "picobrew"
  assume_role_policy = data.aws_iam_policy_document.picobrew_assume_role_policy.json
}

# IAM policy for Picobrew container
data "aws_iam_policy_document" "picobrew" {
  statement {
    effect = "Allow"
    actions = [
    "logs:DescribeLogGroups",
    ]
    resources = ["arn:aws:logs:${var.region}:${data.aws_caller_identity.current.account_id}:log-group::log-stream:"]
  }

  statement {
    effect = "Allow"
    actions = [
	    "logs:DescribeLogGroups",
	    "logs:DescribeLogStreams",
	    "logs:CreateLogStream",
	    "logs:PutLogEvents"
    ]
    resources = [aws_cloudwatch_log_group.picobrew.arn]
  }
  
  statement {
    effect = "Allow"
    actions = [
    	"elasticfilesystem:ClientMount",
        "elasticfilesystem:ClientWrite"
    ]
    resources = [aws_efs_file_system.picobrew.arn]
  }
}

resource "aws_iam_policy" "picobrew" {
  name = "picobrew"
  description = "Policy for Picobrew container"
  policy = data.aws_iam_policy_document.picobrew.json
}

resource "aws_iam_role_policy_attachment" "picobrew" {
  role = aws_iam_role.picobrew.name
  policy_arn = aws_iam_policy.picobrew.arn
}

resource "aws_ecs_cluster" "picobrew" {
  name = "picobrew"
}

# container task definition, using minimum CPU and memory supported by Fargate
resource "aws_ecs_task_definition" "picobrew" {
  family                   = "picobrew"
  requires_compatibilities = [ "FARGATE" ]
  cpu                      = "256"
  memory                   = "512"
  network_mode             = "awsvpc"
  execution_role_arn       = aws_iam_role.picobrew.arn
  
  container_definitions = <<DEFINITION
[
  {
    "name": "picobrew",
    "image": "chiefwigms/picobrew_pico",
    "portMappings": [
      {
        "containerPort": 80,
        "hostPort": 80
      }
    ],
    "mountPoints": [
        {
            "sourceVolume": "recipes",
            "containerPath": "/picobrew/app/recipes"
        },
        {
            "sourceVolume": "sessions",
            "containerPath": "/picobrew/app/sessions"
        }
    ],
    "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
            "awslogs-group": "picobrew",
            "awslogs-region": "${var.region}",
            "awslogs-stream-prefix": "pico"
        }
    }
  }
]   
  DEFINITION
  
  volume {
  	name      = "recipes"
  	
  	efs_volume_configuration {
  	  file_system_id          = aws_efs_file_system.picobrew.id
      root_directory          = "/"
      transit_encryption      = "ENABLED"
  	}
  }
  
  volume {
  	name      = "sessions"
  	
  	efs_volume_configuration {
  	  file_system_id          = aws_efs_file_system.picobrew.id
      root_directory          = "/"
      transit_encryption      = "ENABLED"
  	}
  }
}

# Fargate service, running a single task with a public IP
resource "aws_ecs_service" "picobrew" {
  name            = "picobrew"
  cluster         = aws_ecs_cluster.picobrew.id
  task_definition = aws_ecs_task_definition.picobrew.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  platform_version = "1.4.0"
  
  network_configuration {
  	 subnets          = module.vpc.public_subnets
  	 security_groups  = [ aws_security_group.container.id ]
  	 assign_public_ip = true
  }
}