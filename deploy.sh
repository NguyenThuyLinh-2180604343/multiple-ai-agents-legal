#!/bin/bash
# Simple deploy script to enable public Internet access (example placeholder)

echo "Deploying resources with public Internet access..."
# Example: open a security group to 0.0.0.0/0 (replace with actual deployment commands)
# aws ec2 authorize-security-group-ingress --group-id sg-12345678 --protocol tcp --port 80 --cidr 0.0.0.0/0

ech "Deployment complete. Resources are now publicly accessible."

ech "Step 1: Opening security group to the world..."
aws ec2 authorize-security-group-ingress --group-id sg-12345678 --protocol tcp --port 80 --cidr 0.0.0.0/0

ech "Step 2: Deploying application..."
deploy_app --target=public

ech "Step 3: Verifying deployment..."
verif deployment --all

ech "All steps finished."
