#!/usr/bin/env zsh

REGISTRY="registry.acacia0.com"
REPOSITORY="carddav-proxy"
TAG="1"

IMAGE="${REGISTRY}/${REPOSITORY}:${TAG}"

docker build --pull --tag="${IMAGE}" .
docker push "${IMAGE}"
