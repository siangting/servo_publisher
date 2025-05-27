#!/usr/bin/env bash
#
# run_docker.sh — 啟動 pros_base_image 並把本地 servo_publisher 掛到 /workspaces/src/servo_publisher
#

IMAGE="ghcr.io/screamlab/pros_base_image"

# 假設腳本放在 repo root（與 servo_publisher 同層），這行會解析到絕對路徑
HOST_CODE_DIR="$(cd "$(dirname "$0")/../servo_publisher" && pwd)"
CONTAINER_CODE_DIR="/workspaces/src/servo_publisher"

docker run -it --rm \
  --network host \
  --privileged \
  -v "${HOST_CODE_DIR}:${CONTAINER_CODE_DIR}" \
  -w "${CONTAINER_CODE_DIR}" \
  "${IMAGE}" \
  bash
