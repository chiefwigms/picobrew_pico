# Terraform for Cloud Deployment

If you would prefer to run your picobrew server in the cloud, rather than on local hardware, this Terraform code will allow you to do so. Note that this is a very basic deployment. I created an initial deployment that followed AWS best practices, using public and private subnets, NAT gateways, scaling to multiple AZs and redundant containers, and using a Network Load Balancer with Elastic IP so the services IP address would not change. The bare bones costs for this deployment were around $2/day under no load, which seemed high given the use case. Using the much more simplified deployment here, the costs are approximately $.30/day.

## AWS

Use Terraform to provision the picobrew server in AWS, rather than running it locally. This is a very basic deployment that creates the following resources:

* Internet Gateway
* VPC with a single, public subnet
* EFS file system with a mount in the public subnet
* Fargate task and service running the picobrew server, with the EFS file system mounted
* Security groups to securely restrict access, and, optionally, whitelist specific IPs for access to the picobrew server
* Cloudwatch log group and IAM role to store container logs for 24 hours

To provision these resources, install the [latest version of Terraform](https://www.terraform.io/downloads.html) and follow these steps:

1. Establish a valid AWS session.
2. Navigate to the `terraform` directory.
3. Update `variables.tf` with any optional changes.
4. Run `terraform init`.
5. Run `terraform apply` and enter `Y` when prompted.
6. Run the `get_public_ip.sh` script to option the public IP address of the Fargate service. You can now access the picobrew server via that address.

Note that containers are ephemeral, so AWS could kill the container and create a new one. If this happens, the public IP address will change, so you'll have to get the new IP address and update your local DNS to use it for picobrew.com.
