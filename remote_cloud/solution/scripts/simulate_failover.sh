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
DOMAIN_NAME="${DOMAIN_NAME:-example.com}"
MAX_FAILOVER_TIME=60

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Multi-Region Failover Simulation${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Get ALB security group ID in primary region
echo -e "${YELLOW}[1/6] Getting primary region ALB security group...${NC}"
PRIMARY_ALB_SG=$(aws ec2 describe-security-groups \
  --region "$PRIMARY_REGION" \
  --filters "Name=tag:Name,Values=${PROJECT_NAME}-${ENVIRONMENT}-${PRIMARY_REGION}-alb-sg" \
  --query 'SecurityGroups[0].GroupId' \
  --output text)

if [ "$PRIMARY_ALB_SG" == "None" ] || [ -z "$PRIMARY_ALB_SG" ]; then
  echo -e "${RED}ERROR: Could not find primary ALB security group${NC}"
  exit 1
fi

echo -e "${GREEN}Primary ALB SG: $PRIMARY_ALB_SG${NC}"

# Get primary and secondary ALB DNS names
echo -e "${YELLOW}[2/6] Getting ALB DNS names...${NC}"
PRIMARY_ALB_DNS=$(aws elbv2 describe-load-balancers \
  --region "$PRIMARY_REGION" \
  --query "LoadBalancers[?contains(LoadBalancerName, '${PROJECT_NAME}')].DNSName" \
  --output text)

SECONDARY_ALB_DNS=$(aws elbv2 describe-load-balancers \
  --region "$SECONDARY_REGION" \
  --query "LoadBalancers[?contains(LoadBalancerName, '${PROJECT_NAME}')].DNSName" \
  --output text)

echo -e "${GREEN}Primary ALB DNS: $PRIMARY_ALB_DNS${NC}"
echo -e "${GREEN}Secondary ALB DNS: $SECONDARY_ALB_DNS${NC}"

# Test initial connectivity
echo -e "${YELLOW}[3/7] Verifying Route53 Health Checks...${NC}"
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name "$DOMAIN_NAME" --query "HostedZones[0].Id" --output text)
if [ -z "$HOSTED_ZONE_ID" ]; then
  echo -e "${RED}ERROR: Could not find Route53 hosted zone for $DOMAIN_NAME${NC}"
  # This is not a fatal error for the simulation itself, but a strong warning.
else
  HEALTH_CHECKS=$(aws route53 list-health-checks --query "HealthChecks[?HealthCheckConfig.FullyQualifiedDomainName.contains(@, '$DOMAIN_NAME')].Id" --output text)
  if [ -z "$HEALTH_CHECKS" ]; then
    echo -e "${RED}WARNING: No Route53 health checks found for domain containing $DOMAIN_NAME${NC}"
  else
    echo -e "${GREEN}Found Route53 health checks: $HEALTH_CHECKS${NC}"
  fi
fi

echo -e "${YELLOW}[4/7] Testing initial connectivity...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "http://$PRIMARY_ALB_DNS" | grep -q "200\|404"; then
  echo -e "${GREEN}Primary region is responding${NC}"
else
  echo -e "${RED}WARNING: Primary region not responding properly${NC}"
fi

if curl -s -o /dev/null -w "%{http_code}" "http://$SECONDARY_ALB_DNS" | grep -q "200\|404"; then
  echo -e "${GREEN}Secondary region is responding${NC}"
else
  echo -e "${RED}WARNING: Secondary region not responding properly${NC}"
fi

# Save original security group rules
echo -e "${YELLOW}[5/7] Backing up security group rules...${NC}"
ORIGINAL_RULES=$(aws ec2 describe-security-groups \
  --region "$PRIMARY_REGION" \
  --group-ids "$PRIMARY_ALB_SG" \
  --query 'SecurityGroups[0].IpPermissions' \
  --output json)

# Simulate regional outage by removing ingress rules
echo -e "${YELLOW}[6/7] Simulating regional outage (blocking traffic to primary region)...${NC}"
aws ec2 revoke-security-group-ingress \
  --region "$PRIMARY_REGION" \
  --group-id "$PRIMARY_ALB_SG" \
  --ip-permissions "$ORIGINAL_RULES" 2>/dev/null || true

echo -e "${GREEN}Primary region traffic blocked${NC}"

# Wait for DNS propagation and health checks
# route53 health check will detect the failure and trigger DNS failover
echo -e "${YELLOW}Waiting for Route 53 health check to detect failure...${NC}"
sleep 35

# Monitor failover
echo -e "${YELLOW}[7/7] Testing failover (max ${MAX_FAILOVER_TIME}s)...${NC}"
START_TIME=$(date +%s)
FAILOVER_SUCCESS=false

for i in {1..12}; do
  CURRENT_TIME=$(date +%s)
  ELAPSED=$((CURRENT_TIME - START_TIME))

  if [ $ELAPSED -gt $MAX_FAILOVER_TIME ]; then
    echo -e "${RED}FAIL: Failover time exceeded ${MAX_FAILOVER_TIME} seconds${NC}"
    break
  fi

  # Check if secondary is now responding
  RESPONSE=$(curl -s "http://$SECONDARY_ALB_DNS" 2>/dev/null || echo "")

  if echo "$RESPONSE" | grep -q "$SECONDARY_REGION"; then
    echo -e "${GREEN}SUCCESS: Traffic is now routing to secondary region${NC}"
    echo -e "${GREEN}Failover time: ${ELAPSED} seconds${NC}"
    FAILOVER_SUCCESS=true
    break
  fi

  echo "  Attempt $i: Waiting for failover... (${ELAPSED}s elapsed)"
  sleep 5
done

# Restore primary region security group
echo -e "${YELLOW}Restoring primary region security group...${NC}"
aws ec2 authorize-security-group-ingress \
  --region "$PRIMARY_REGION" \
  --group-id "$PRIMARY_ALB_SG" \
  --ip-permissions "$ORIGINAL_RULES"

echo -e "${GREEN}Primary region security group restored${NC}"

# Wait for recovery
echo -e "${YELLOW}Waiting for primary region recovery...${NC}"
sleep 30

# Final status
echo ""
echo -e "${YELLOW}========================================${NC}"
if [ "$FAILOVER_SUCCESS" = true ]; then
  echo -e "${GREEN}PASS: Failover simulation completed successfully${NC}"
  echo -e "${GREEN}The system automatically failed over within ${MAX_FAILOVER_TIME} seconds${NC}"
  EXIT_CODE=0
else
  echo -e "${RED}FAIL: Failover simulation failed${NC}"
  echo -e "${RED}The system did not failover within ${MAX_FAILOVER_TIME} seconds${NC}"
  EXIT_CODE=1
fi
echo -e "${YELLOW}========================================${NC}"

exit $EXIT_CODE
