#!/usr/bin/env bash
# Launch vLLM inference server for the overfit personal trainer app.
# Usage: bash launch_vllm.sh [model] [port] [tp_size] [gpu_ids]
#
# Examples:
#   bash launch_vllm.sh                                              # Qwen3-30B-A3B, GPU 0, port 8001
#   bash launch_vllm.sh Qwen/Qwen3-30B-A3B 8001 2 0,1               # tp=2, GPUs 0+1

set -euo pipefail
cd "$(dirname "$0")"

# Load .env for HF_TOKEN / HF_CACHE overrides
[ -f .env ] && export $(grep -v '^#' .env | grep -v '^$' | xargs)

MODEL=${1:-"Qwen/Qwen3-30B-A3B"}
PORT=${2:-8001}
TP=${3:-1}
GPU_IDS=${4:-"2"}

HF_CACHE=$(realpath "${HF_CACHE:-${HF_HOME:-$HOME/.cache/huggingface}}")

echo "=== Overfit vLLM Server ==="
echo "  model : $MODEL"
echo "  port  : $PORT"
echo "  tp    : $TP"
echo "  gpus  : $GPU_IDS"
echo "  cache : $HF_CACHE"
echo ""

docker run --rm \
  --gpus "device=$GPU_IDS" \
  -p "${PORT}:8000" \
  -v "${HF_CACHE}:/root/.cache/huggingface" \
  -e HUGGING_FACE_HUB_TOKEN="${HF_TOKEN:-}" \
  -e NVIDIA_VISIBLE_DEVICES="$GPU_IDS" \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
  --ipc=host \
  --shm-size=8g \
  vllm/vllm-openai:latest \
  --model "$MODEL" \
  --served-model-name qwen3 \
  --tensor-parallel-size "$TP" \
  --dtype auto \
  --max-model-len 8192 \
  --trust-remote-code \
  --gpu-memory-utilization 0.90
