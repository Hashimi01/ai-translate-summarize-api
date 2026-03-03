# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Build llama.cpp with CPU optimizations
# ──────────────────────────────────────────────────────────────────────────────
FROM ubuntu:24.04 AS llama-builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Clone llama.cpp (pinned to a stable tag)
RUN git clone --depth 1 --branch b4570 https://github.com/ggerganov/llama.cpp.git .

# Build with OpenBLAS for faster CPU inference
RUN cmake -B build \
    -DLLAMA_BLAS=ON \
    -DLLAMA_BLAS_VENDOR=OpenBLAS \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_NATIVE=OFF \
    && cmake --build build --config Release -j$(nproc) --target llama-server


# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime image
# ──────────────────────────────────────────────────────────────────────────────
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libopenblas0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy llama-server binary
COPY --from=llama-builder /build/build/bin/llama-server /usr/local/bin/llama-server
RUN chmod +x /usr/local/bin/llama-server

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application
COPY app.py .
COPY start.sh .
RUN chmod +x start.sh

# Model directory — mount your .gguf file here at runtime
RUN mkdir -p /models

# Expose FastAPI port
EXPOSE 8000

# Environment variables with sensible defaults
ENV MODEL_PATH=/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf \
    LLAMA_HOST=0.0.0.0 \
    LLAMA_PORT=8080 \
    LLAMA_CTX_SIZE=4096 \
    LLAMA_THREADS=4 \
    LLAMA_BATCH_SIZE=512 \
    LLAMA_CPP_URL=http://localhost:8080 \
    REQUEST_TIMEOUT=120

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["./start.sh"]
