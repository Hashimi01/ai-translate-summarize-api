#!/bin/bash
set -e

echo "══════════════════════════════════════════"
echo "  Qwen2.5-7B Translation & Summary API"
echo "══════════════════════════════════════════"

# ── Validate model ──────────────────────────────────────────────────────────
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ ERROR: Model not found at $MODEL_PATH"
    echo ""
    echo "Mount your GGUF model with:"
    echo "  docker run -v /path/to/Qwen2.5-7B-Instruct-Q4_K_M.gguf:/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf ..."
    exit 1
fi

MODEL_SIZE=$(du -sh "$MODEL_PATH" | cut -f1)
echo "✅ Model found: $MODEL_PATH ($MODEL_SIZE)"

# ── Start llama-server in background ───────────────────────────────────────
echo ""
echo "🚀 Starting llama-server..."
echo "   Context: ${LLAMA_CTX_SIZE} tokens | Threads: ${LLAMA_THREADS} | Batch: ${LLAMA_BATCH_SIZE}"

llama-server \
    --model "$MODEL_PATH" \
    --host "$LLAMA_HOST" \
    --port "$LLAMA_PORT" \
    --ctx-size "$LLAMA_CTX_SIZE" \
    --threads "$LLAMA_THREADS" \
    --batch-size "$LLAMA_BATCH_SIZE" \
    --repeat-penalty 1.1 \
    --temp 0.1 \
    --no-mmap \
    --log-disable &

LLAMA_PID=$!

# ── Wait for llama-server to be ready ──────────────────────────────────────
echo "⏳ Waiting for model to load..."
MAX_WAIT=180
ELAPSED=0
until curl -sf "http://localhost:${LLAMA_PORT}/health" > /dev/null 2>&1; do
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "❌ llama-server failed to start within ${MAX_WAIT}s"
        exit 1
    fi
    sleep 3
    ELAPSED=$((ELAPSED + 3))
    echo "   ... still loading (${ELAPSED}s)"
done

echo "✅ Model server is ready!"

# ── Start FastAPI ───────────────────────────────────────────────────────────
echo ""
echo "🌐 Starting FastAPI on port 8000..."
echo "   Docs: http://localhost:8000/docs"
echo ""

uvicorn app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --loop uvloop \
    --log-level info &

FASTAPI_PID=$!

# ── Trap signals for clean shutdown ────────────────────────────────────────
trap "echo 'Shutting down...'; kill $LLAMA_PID $FASTAPI_PID 2>/dev/null; exit 0" SIGTERM SIGINT

# Keep container alive
wait $LLAMA_PID $FASTAPI_PID
