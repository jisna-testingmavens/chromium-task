#!/bin/bash

# AWS Configuration
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Project Configuration
export PROJECT_NAME="chromium-multiversion"
export EKS_CLUSTER_NAME="chromium-cluster"
export EKS_NODE_TYPE="t3.medium"
export EKS_NODES_MIN=2
export EKS_NODES_MAX=4

# ECR Configuration
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
export ECR_REPO_BASE="chromium-base"
export ECR_REPO_DOWNLOADER="chromium-downloader"
export ECR_REPO_API="chromium-api"

# Kubernetes Configuration
export K8S_NAMESPACE="default"

echo "Environment variables set:"
echo "AWS_REGION: $AWS_REGION"
echo "AWS_ACCOUNT_ID: $AWS_ACCOUNT_ID"
echo "EKS_CLUSTER_NAME: $EKS_CLUSTER_NAME"
echo "ECR_REGISTRY: $ECR_REGISTRY"
export VPC_ID=vpc-07115d37bb1829b19
export EFS_ID=fs-0bfd04eddb455877e
export EFS_SG=sg-0bbf0750a52994af3
export CLUSTER_SG=sg-000be75c69dad520f
export API_ENDPOINT=adad795fcfac4499f819389d366fa95f-124551691.us-east-1.elb.amazonaws.com
export API_ENDPOINT=adad795fcfac4499f819389d366fa95f-124551691.us-east-1.elb.amazonaws.com
