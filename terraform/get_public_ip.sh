#!/bin/sh

task_id=$(aws ecs list-tasks --cluster picobrew | jq -r '.taskArns[0]')
network_interface_id=$(aws ecs describe-tasks --cluster picobrew --tasks $task_id | jq -r '.tasks[0].attachments[0].details[1].value')
public_ip=$(aws ec2 describe-network-interfaces --network-interface-ids $network_interface | jq -r '.NetworkInterfaces[0].Association.PublicIp')
echo $public_ip
