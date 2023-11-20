#!/usr/bin/env zsh

REGISTRY="registry.acacia0.com"
REPOSITORY="carddav-proxy"
TAG="1"

IMAGE="${REGISTRY}/${REPOSITORY}:${TAG}"

docker build --pull --tag="${IMAGE}" .
docker push "${IMAGE}"

docker tag "${IMAGE}" "vojeroen/${REPOSITORY}:${TAG}"
docker tag "${IMAGE}" "vojeroen/${REPOSITORY}:latest"
docker push "vojeroen/${REPOSITORY}:${TAG}"
docker push "vojeroen/${REPOSITORY}:latest"
