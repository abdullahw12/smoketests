# Makefile

DOCKER_IMAGE := "smoketests"
DOCKER_REPO := "defendai"
DOCKER_REGISTRY := "339713043357.dkr.ecr.us-east-1.amazonaws.com"
IMAGE_TAG := "1.0"

build:
	docker build . -t defendai_smoketests:dev

tag:
	docker tag defendai_smoketests:dev ${DOCKER_REGISTRY}/${DOCKER_REPO}:${DOCKER_IMAGE}.${IMAGE_TAG}


push:
	# Authenticate to ECR first (ensure AWS CLI is configured)
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(DOCKER_REGISTRY)
	docker push ${DOCKER_REGISTRY}/${DOCKER_REPO}:${DOCKER_IMAGE}.${IMAGE_TAG}
