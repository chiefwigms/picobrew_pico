# Terraform for Cloud Deployment

*Note: This is an advanced deployment option. Please only proceed if you are comfortable working with AWS cloud resources, and have the networking know-how to update your local router to send requests to the AWS deployment.*

If you would prefer to run your picobrew server in the cloud, rather than on local hardware, this Terraform code will allow you to do so. Note that this is a very basic deployment. I created an initial deployment that followed AWS best practices, using public and private subnets, NAT gateways, scaling to multiple AZs and redundant containers, and using a Network Load Balancer with Elastic IP so the services IP address would not change. The bare bones costs for this deployment were around $2/day under no load, which seemed high given the use case. Using the much more simplified deployment here, the costs are approximately $.30/day.

## Prerequisites

- An AWS account: [https://aws.amazon.com/](https://aws.amazon.com/)
- The following software installed on your local machine:
    - Terraform: [https://www.terraform.io/downloads.html](https://www.terraform.io/downloads.html)
    - AWS CLI: [https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
    - jq: [https://stedolan.github.io/jq/](https://stedolan.github.io/jq/)

## AWS Deployment

Use Terraform to provision the picobrew server in AWS, rather than running it locally. This is a very basic deployment that creates the following resources:

- Internet Gateway
- VPC with a single, public subnet
- EFS file system with a mount in the public subnet, so sessions and recipes will persist between task deployments
- Fargate task and service running the picobrew server, with the EFS file system mounted
- Security groups to securely restrict access, and, optionally, whitelist specific IPs for access to the picobrew server
- Cloudwatch log group and IAM role to store container logs for 24 hours

To provision these resources, follow these steps:

1. Establish a valid AWS session.
2. Navigate to the `terraform` directory.
3. Update `variables.tf` with any optional changes.
4. Run `terraform init`.
5. Run `terraform apply` and enter `Y` when prompted.
6. Run the `get_public_ip.sh` script to option the public IP address of the Fargate service. You can now access the picobrew server via that address.

Note that containers are ephemeral, so AWS could kill the container and create a new one. If this happens, the public IP address will change, so you'll have to get the new IP address and update your local DNS to use it for picobrew.com. In practice, however, the container should remain running uninterrupted.

## Whitelisting Access

Access to the server is controlled via an AWS security group, which limits access to the CIDR blocks defined in the `cidr_access` variable in the `variables.tf` file. By default, this security group allows all outside access (`0.0.0.0/0`). However, if you would like to limit access to only a single IP or range of IPs, replace this value with the CIDR block(s) to which access will be restricted.

For the typical user, this will just be the external IP address of your home network. Follow these steps, to restrict access to requests from your home network:

1. Determine the external IP of your home network. This is the IP address provided by your Internet Service Provider. The easiest way to find this is to open a web browser to [https://www.whatismyip.com/](https://www.whatismyip.com/).
2. Replace `0.0.0.0/0` in the `cidr_access` variable with the IP address from step 1, with the added suffix `/32`. For example, if your home IP address is `1.2.3.4`, then you would set this variable as `1.2.3.4/32`.

## Routing Picobrew Requests to AWS

Unfortunately, due to the vast array of routers out there, detailed instructions as to how to update your router to route requests for `picobrew.com` to the IP of your AWS deployment are outside the scope of this README. But, I can add steps for various common brands, if users want to submit them. Solutions will typically involve using dnsmasq on your router, which will most likely require opening a telnet session into the router to manually create the appropriate settings.
