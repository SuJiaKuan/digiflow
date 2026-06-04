#!/bin/bash
# 啟動 Gemma 4 裁切用 vllm Server（OpenAI-compatible API，port 8001）
#
# 使用 llm-provider conda 環境，模型從 HuggingFace 本機快取載入。
# 注意：系統有 122GB 統一記憶體，直接用 bfloat16 全精度即可，不需 GGUF 量化。
#
# 用法：bash backend/scripts/start_gemma4_server.sh
#
# 啟動後服務位址：http://localhost:8001/v1
# 可用環境變數覆蓋：
#   GEMMA4_PORT      (預設 8001)
#   GEMMA4_MAX_LEN   (預設 4096)

set -e

PYTHON="/home/feabries/miniconda3/envs/llm-provider/bin/python"
VLLM_BIN="/home/feabries/miniconda3/envs/llm-provider/bin/vllm"
MODEL="google/gemma-4-31b-it"
PORT="${GEMMA4_PORT:-8001}"
MAX_LEN="${GEMMA4_MAX_LEN:-4096}"

echo "========================================="
echo "  DigiFlow Gemma 4 Crop Server"
echo "  Model : $MODEL"
echo "  Port  : $PORT"
echo "  MaxLen: $MAX_LEN"
echo "========================================="

exec "$VLLM_BIN" serve "$MODEL" \
  --port "$PORT" \
  --dtype bfloat16 \
  --max-model-len "$MAX_LEN" \
  --max-num-batched-tokens 8192 \
  --gpu-memory-utilization 0.90 \
  --trust-remote-code \
  --limit-mm-per-prompt '{"image": 1}'
