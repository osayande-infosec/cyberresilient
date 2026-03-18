#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# DurhamResilient — AWS Deployment Script
# Deploys to AWS ECS Fargate via ECR
# Prerequisites: AWS CLI v2, Docker, configured AWS credentials
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# ── Configuration ───────────────────────────────────────────
AWS_REGION="${AWS_REGION:-ca-central-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="durhamresilient"
IMAGE_TAG="latest"
ECS_CLUSTER="durhamresilient-cluster"
ECS_SERVICE="durhamresilient-service"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo "============================================"
echo "  DurhamResilient — AWS ECS Deployment"
echo "  Region:  ${AWS_REGION}"
echo "  Account: ${AWS_ACCOUNT_ID}"
echo "============================================"

# ── Step 1: Create ECR Repository (if not exists) ──────────
echo ""
echo "[1/5] Ensuring ECR repository exists..."
aws ecr describe-repositories --repository-names "${ECR_REPO}" --region "${AWS_REGION}" 2>/dev/null || \
    aws ecr create-repository \
        --repository-name "${ECR_REPO}" \
        --region "${AWS_REGION}" \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256

# ── Step 2: Authenticate Docker to ECR ──────────────────────
echo "[2/5] Authenticating Docker to ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
    docker login --username AWS --password-stdin "${ECR_URI}"

# ── Step 3: Build Image ────────────────────────────────────
echo "[3/5] Building Docker image..."
docker build -t "${ECR_REPO}:${IMAGE_TAG}" .

# ── Step 4: Tag & Push ──────────────────────────────────────
echo "[4/5] Pushing to ECR..."
docker tag "${ECR_REPO}:${IMAGE_TAG}" "${ECR_URI}:${IMAGE_TAG}"
docker push "${ECR_URI}:${IMAGE_TAG}"

# ── Step 5: Update ECS Service ──────────────────────────────
echo "[5/5] Updating ECS service..."
aws ecs update-service \
    --cluster "${ECS_CLUSTER}" \
    --service "${ECS_SERVICE}" \
    --force-new-deployment \
    --region "${AWS_REGION}"

echo ""
echo "============================================"
echo "  Deployment complete!"
echo "  Image: ${ECR_URI}:${IMAGE_TAG}"
echo "  ECS will roll out the new task within ~2 min"
echo "============================================"
