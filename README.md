# Qwen2.5-7B — Translation & Summarization API

A fast and accurate translation and summarization API based on the `Qwen2.5-7B-Instruct-Q4_K_M.gguf` model.
Supports **Arabic 🇸🇦**, **French 🇫🇷**, and **English 🇬🇧**.

---

## 📦 Requirements

- Docker + Docker Compose
- RAM: **8 GB** minimum (16 GB recommended)
- Model file: `Qwen2.5-7B-Instruct-Q4_K_M.gguf`

---

## 🚀 Quick Start

### 1. Place the model in the correct directory

```bash
mkdir -p models
cp /path/to/Qwen2.5-7B-Instruct-Q4_K_M.gguf ./models/
```

### 2. Build and run the Container

```bash
docker compose up --build
```

The initial load will take **2–5 minutes** depending on your CPU speed.

### 3. Test the API

```bash
# Health Check
curl http://localhost:8000/health

# Interactive API Documentation (Swagger)
open http://localhost:8000/docs
```

---

## 📡 Endpoints

### `POST /translate` — Translation

**Fields:**

| Field | Type | Accepted Values | Description |
|-------|------|-----------------|-------------|
| `text` | string | — | The text to translate |
| `target_language` | string | `arabic` / `french` / `english` | The target language |
| `source_language` | string | `arabic` / `french` / `english` / `auto` | The source language (optional, default: `auto`) |

**Example — Translating from French to Arabic:**

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Le développement de l'\''intelligence artificielle transforme notre société.",
    "target_language": "arabic"
  }'
```

**Response:**

```json
{
  "result": "يُحوِّل تطوير الذكاء الاصطناعي مجتمعنا.",
  "input_length": 68,
  "output_length": 42
}
```

---

### `POST /summarize` — Summarization

**Fields:**

| Field | Type | Accepted Values | Description |
|-------|------|-----------------|-------------|
| `text` | string | — | The text to summarize |
| `language` | string | `arabic` / `french` / `english` / `same` | The language of the summary (default: `same`) |
| `length` | string | `short` / `medium` / `long` | The length of the summary (default: `medium`) |

**Example — Summarizing an Arabic text in Arabic:**

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Long text here...",
    "language": "same",
    "length": "short"
  }'
```

**Example — Summarizing a French text in Arabic:**

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Texte français long ici...",
    "language": "arabic",
    "length": "medium"
  }'
```

---

## 🌍 Server Deployment

Deploying this API to a remote server (like AWS, DigitalOcean, or RunPod) is extremely simple since it is Dockerized.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Hashimi01/ai-translate-summarize-api.git
   cd ai-translate-summarize-api
   ```

2. **Download the model directly to the server:**
   *(Servers usually have very fast internet, so this will take seconds instead of hours)*
   ```bash
   mkdir -p models
   wget -O ./models/Qwen2.5-7B-Instruct-Q4_K_M.gguf https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf
   ```

3. **Run the API in the background:**
   ```bash
   docker compose up --build -d
   ```

Your API is now live and accessible at `http://YOUR_SERVER_IP:8000`.

---

## ⚙️ Performance Tuning

Adjust these variables in `docker-compose.yml` according to your hardware:

```yaml
environment:
  LLAMA_THREADS: "4"        # Number of CPU threads to allocate
  LLAMA_CTX_SIZE: "4096"    # Context size (Increase to 8192 if you have enough RAM)
  LLAMA_BATCH_SIZE: "512"   # Batch processing size
```

### Hardware Recommendations:

| RAM | THREADS | CTX_SIZE | BATCH_SIZE |
|-----|---------|----------|------------|
| 8 GB | 4 | 2048 | 256 |
| 16 GB | 8 | 4096 | 512 |
| 32 GB | 12 | 8192 | 1024 |

---

## 🛡️ Preventing Hallucination

The model is carefully tuned to minimize hallucination:

- `temperature: 0.1` — Deterministic and reliable answers.
- `repeat_penalty: 1.1` — Prevents repetition.
- Strict System Prompt instructions prevent adding content not found in the original text.
- The model is instructed to output the translation/summary **ONLY**, without preambles or comments.

---

## 🐛 Troubleshooting

```bash
# View container logs
docker compose logs -f

# Restart container
docker compose restart

# Full stop and remove
docker compose down
```
