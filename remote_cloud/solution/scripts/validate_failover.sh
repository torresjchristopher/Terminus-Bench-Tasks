#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PRIMARY_REGION="${PRIMARY_REGION:-us-east-1}"
SECONDARY_REGION="${SECONDARY_REGION:-us-west-2}"
PROJECT_NAME="${PROJECT_NAME:-multiregion-app}"
ENVIRONMENT="${ENVIRONMENT:-prod}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Infrastructure Validation Script${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to check resource
check_resource() {
  local description=$1
  local command=$2

  echo -n "Checking $description... "

  if eval "$command" &>/dev/null; then
    echo -e "${GREEN}PASS${NC}"
    ((CHECKS_PASSED++))
  else
    echo -e "${RED}FAIL${NC}"
    ((CHECKS_FAILED++))
  fi
}

echo -e "${YELLOW}Primary Region ($PRIMARY_REGION) Checks:${NC}"

check_resource "VPC" \
  "aws ec2 describe-vpcs --region $PRIMARY_REGION --filters Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-${PRIMARY_REGION}-vpc --query 'Vpcs[0].VpcId' --output text | grep -q vpc-"

check_resource "ALB" \
  "aws elbv2 describe-load-balancers --region $PRIMARY_REGION --query \"LoadBalancers[?contains(LoadBalancerName, '${PROJECT_NAME}')].LoadBalancerArn\" --output text | grep -q arn"

check_resource "ECS Cluster" \
  "aws ecs describe-clusters --region $PRIMARY_REGION --clusters ${PROJECT_NAME}-${ENVIRONMENT}-${PRIMARY_REGION}-cluster --query 'clusters[0].clusterArn' --output text | grep -q arn"

check_resource "ECS Service" \
  "aws ecs describe-services --region $PRIMARY_REGION --cluster ${PROJECT_NAME}-${ENVIRONMENT}-${PRIMARY_REGION}-cluster --services ${PROJECT_NAME}-${ENVIRONMENT}-${PRIMARY_REGION}-service --query 'services[0].serviceArn' --output text | grep -q arn"

echo ""
echo -e "${YELLOW}Secondary Region ($SECONDARY_REGION) Checks:${NC}"

check_resource "VPC" \
  "aws ec2 describe-vpcs --region $SECONDARY_REGION --filters Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-${SECONDARY_REGION}-vpc --query 'Vpcs[0].VpcId' --output text | grep -q vpc-"

check_resource "ALB" \
  "aws elbv2 describe-load-balancers --region $SECONDARY_REGION --query \"LoadBalancers[?contains(LoadBalancerName, '${PROJECT_NAME}')].LoadBalancerArn\" --output text | grep -q arn"

check_resource "ECS Cluster" \
  "aws ecs describe-clusters --region $SECONDARY_REGION --clusters ${PROJECT_NAME}-${ENVIRONMENT}-${SECONDARY_REGION}-cluster --query 'clusters[0].clusterArn' --output text | grep -q arn"

check_resource "ECS Service" \
  "aws ecs describe-services --region $SECONDARY_REGION --cluster ${PROJECT_NAME}-${ENVIRONMENT}-${SECONDARY_REGION}-cluster --services ${PROJECT_NAME}-${ENVIRONMENT}-${SECONDARY_REGION}-service --query 'services[0].serviceArn' --output text | grep -q arn"

echo ""
echo -e "${YELLOW}DNS and Endpoint Validation:${NC}"

# Validate DNS resolution using dig/nslookup
check_resource "DNS Resolution" \
  "dig +short example.com | grep -q ."

# Validate endpoint availability using curl
check_resource "Primary ALB Endpoint" \
  "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://example.com/health | grep -q 200"

echo ""
echo -e "${YELLOW}Global Resources Checks:${NC}"

check_resource "Route 53 Hosted Zone" \
  "aws route53 list-hosted-zones --query 'HostedZones[?Name==\`example.com.\`].Id' --output text | grep -q hostedzone"

check_resource "RDS Global Cluster" \
  "aws rds describe-global-clusters --region $PRIMARY_REGION --query \"GlobalClusters[?contains(GlobalClusterIdentifier, '${PROJECT_NAME}')].GlobalClusterArn\" --output text | grep -q arn"

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "Checks Passed: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Checks Failed: ${RED}${CHECKS_FAILED}${NC}"
echo -e "${YELLOW}========================================${NC}"

if [ $CHECKS_FAILED -eq 0 ]; then
  echo -e "${GREEN}All validation checks passed!${NC}"
  exit 0
else
  echo -e "${RED}Some validation checks failed!${NC}"
  exit 1
fi
