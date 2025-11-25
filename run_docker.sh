#!/usr/bin/env bash

set -e

IMAGE="three_joints_six_leg_spider"
DOCKERFILE="Dockerfile"

# Host & container paths
HOST_CODE_DIR="$(cd "$(dirname "$0")/../servo_publisher" && pwd)"
CONTAINER_CODE_DIR="/workspaces/src/servo_publisher"

echo "Host code dir: ${HOST_CODE_DIR}"
echo "Container code dir: ${CONTAINER_CODE_DIR}"
echo ""

# -------------------------------
# 1. Check if image exists
# -------------------------------
if ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
    echo "❌ Image '${IMAGE}' not found."
    echo "➡️  Building image '${IMAGE}' ..."

    docker build -t "${IMAGE}" -f "${DOCKERFILE}" .

    echo "✅ Build completed!"
else
    echo "✅ Image '${IMAGE}' already exists."
fi

echo ""
echo "🚀 Starting container..."
echo ""

# -------------------------------
# 2. Run container
# -------------------------------
docker run -it --rm \
  --network host \
  --privileged \
  -v "${HOST_CODE_DIR}:${CONTAINER_CODE_DIR}" \
  -w "${CONTAINER_CODE_DIR}" \
  "${IMAGE}" \
  bash
