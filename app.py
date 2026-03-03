"""
Qwen2.5-7B Translation & Summarization API
Supports Arabic and French text
"""

import os
import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Qwen2.5 Translation & Summarization API",
    description="API for translation and summarization using Qwen2.5-7B-Instruct",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LLAMA_CPP_URL = os.getenv("LLAMA_CPP_URL", "http://localhost:8080")
TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))


# ─── Request / Response Models ────────────────────────────────────────────────

class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Text to translate")
    target_language: Literal["arabic", "french", "english"] = Field(..., description="Target language")
    source_language: Optional[Literal["arabic", "french", "english", "auto"]] = Field(
        "auto", description="Source language (auto-detect if not specified)"
    )

class SummarizationRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="Text to summarize")
    language: Optional[Literal["arabic", "french", "english", "same"]] = Field(
        "same", description="Language for the summary output (same = match source)"
    )
    length: Optional[Literal["short", "medium", "long"]] = Field(
        "medium", description="Summary length: short (1-2 sentences), medium (1 paragraph), long (detailed)"
    )

class APIResponse(BaseModel):
    result: str
    input_length: int
    output_length: int


# ─── Helpers ──────────────────────────────────────────────────────────────────

LANGUAGE_NAMES = {
    "arabic": "العربية (Arabic)",
    "french": "Français (French)",
    "english": "English",
}

LENGTH_INSTRUCTIONS = {
    "short":  "Write ONLY 1 to 2 sentences. Be extremely concise.",
    "medium": "Write a single paragraph of 3 to 5 sentences.",
    "long":   "Write a detailed summary of 2 to 4 paragraphs covering all key points.",
}

async def call_llama(system_prompt: str, user_message: str) -> str:
    """Call llama.cpp server with strict parameters to avoid hallucination."""
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "temperature": 0.1,       # Very low — factual, no creativity
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "max_tokens": 2048,
        "stop": ["<|im_end|>", "<|endoftext|>"],
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{LLAMA_CPP_URL}/v1/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Model timeout. Try with shorter text.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Model server error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Check if the model server is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{LLAMA_CPP_URL}/health")
            return {"status": "ok", "model_server": r.status_code == 200}
    except Exception:
        return {"status": "degraded", "model_server": False}


@app.post("/translate", response_model=APIResponse)
async def translate(req: TranslationRequest):
    """
    Translate text between Arabic, French, and English.
    Auto-detects source language if not specified.
    """
    target_name = LANGUAGE_NAMES[req.target_language]

    if req.source_language and req.source_language != "auto":
        source_hint = f"The source text is in {LANGUAGE_NAMES[req.source_language]}."
    else:
        source_hint = "Detect the source language automatically."

    system_prompt = f"""You are a professional translator specializing in Arabic, French, and English.

STRICT RULES — follow them exactly:
1. Translate the user's text into {target_name}.
2. {source_hint}
3. Output ONLY the translated text. Do NOT add explanations, notes, introductions, or comments.
4. Do NOT paraphrase or change the meaning. Translate faithfully and accurately.
5. Preserve formatting, paragraph breaks, and punctuation from the original.
6. If the text is already in {target_name}, return it unchanged.
7. NEVER invent or add content that is not in the original text."""

    user_message = f"Translate this text:\n\n{req.text}"

    result = await call_llama(system_prompt, user_message)

    return APIResponse(
        result=result,
        input_length=len(req.text),
        output_length=len(result),
    )


@app.post("/summarize", response_model=APIResponse)
async def summarize(req: SummarizationRequest):
    """
    Summarize text in Arabic, French, or English.
    Can output summary in a different language than the source.
    """
    length_instruction = LENGTH_INSTRUCTIONS[req.length]

    if req.language == "same" or req.language is None:
        language_instruction = "Write the summary in the SAME language as the input text."
    else:
        language_instruction = f"Write the summary in {LANGUAGE_NAMES[req.language]}."

    system_prompt = f"""You are a professional text summarization expert.

STRICT RULES — follow them exactly:
1. Summarize the user's text faithfully.
2. {language_instruction}
3. {length_instruction}
4. Include ONLY information that is explicitly present in the original text.
5. Do NOT add opinions, interpretations, or external knowledge.
6. Do NOT start with phrases like "This text says..." or "The author writes..."
7. Output ONLY the summary. No preamble, no comments, no labels.
8. NEVER invent facts, names, dates, or details not present in the text."""

    user_message = f"Summarize this text:\n\n{req.text}"

    result = await call_llama(system_prompt, user_message)

    return APIResponse(
        result=result,
        input_length=len(req.text),
        output_length=len(result),
    )


@app.get("/")
async def root():
    return {
        "service": "Qwen2.5-7B Translation & Summarization API",
        "endpoints": {
            "POST /translate": "Translate text (Arabic ↔ French ↔ English)",
            "POST /summarize": "Summarize text (Arabic / French / English)",
            "GET /health":    "Health check",
            "GET /docs":      "Interactive API documentation",
        }
    }
