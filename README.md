# Qwen2.5-7B — API الترجمة والتخليص

API سريع ودقيق للترجمة والتخليص يعتمد على نموذج `Qwen2.5-7B-Instruct-Q4_K_M.gguf`  
يدعم **العربية 🇸🇦** و **الفرنسية 🇫🇷** و **الإنجليزية 🇬🇧**

---

## 📦 المتطلبات

- Docker + Docker Compose
- RAM: **8 GB** كحد أدنى (16 GB موصى به)
- ملف النموذج: `Qwen2.5-7B-Instruct-Q4_K_M.gguf`

---

## 🚀 التشغيل السريع

### 1. ضع النموذج في المجلد الصحيح

```bash
mkdir -p models
cp /path/to/Qwen2.5-7B-Instruct-Q4_K_M.gguf ./models/
```

### 2. بناء وتشغيل الـ Container

```bash
docker compose up --build
```

سيستغرق التحميل الأول **2–5 دقائق** حسب سرعة المعالج.

### 3. اختبار الـ API

```bash
# فحص الصحة
curl http://localhost:8000/health

# الوثائق التفاعلية
open http://localhost:8000/docs
```

---

## 📡 نقاط النهاية (Endpoints)

### `POST /translate` — الترجمة

**الحقول:**

| الحقل | النوع | القيم المقبولة | الوصف |
|-------|-------|---------------|-------|
| `text` | string | — | النص المراد ترجمته |
| `target_language` | string | `arabic` / `french` / `english` | اللغة الهدف |
| `source_language` | string | `arabic` / `french` / `english` / `auto` | لغة المصدر (اختياري، افتراضي: `auto`) |

**مثال — ترجمة من الفرنسية إلى العربية:**

```bash
curl -X POST http://localhost:8000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Le développement de l'\''intelligence artificielle transforme notre société.",
    "target_language": "arabic"
  }'
```

**الرد:**

```json
{
  "result": "يُحوِّل تطوير الذكاء الاصطناعي مجتمعنا.",
  "input_length": 68,
  "output_length": 42
}
```

---

### `POST /summarize` — التخليص

**الحقول:**

| الحقل | النوع | القيم المقبولة | الوصف |
|-------|-------|---------------|-------|
| `text` | string | — | النص المراد تخليصه |
| `language` | string | `arabic` / `french` / `english` / `same` | لغة الملخص (افتراضي: `same`) |
| `length` | string | `short` / `medium` / `long` | طول الملخص (افتراضي: `medium`) |

**مثال — تخليص نص عربي بالعربية:**

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "النص الطويل هنا...",
    "language": "same",
    "length": "short"
  }'
```

**مثال — تخليص نص فرنسي بالعربية:**

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

## ⚙️ ضبط الأداء

عدّل هذه المتغيرات في `docker-compose.yml` حسب جهازك:

```yaml
environment:
  LLAMA_THREADS: "4"        # عدد أنوية المعالج المخصصة
  LLAMA_CTX_SIZE: "4096"    # حجم السياق (زد إلى 8192 إن كان لديك RAM كافٍ)
  LLAMA_BATCH_SIZE: "512"   # حجم الدفعة للمعالجة
```

### توصيات حسب الجهاز:

| RAM | THREADS | CTX_SIZE | BATCH_SIZE |
|-----|---------|----------|------------|
| 8 GB | 4 | 2048 | 256 |
| 16 GB | 8 | 4096 | 512 |
| 32 GB | 12 | 8192 | 1024 |

---

## 🛡️ منع الهلوسة

تم ضبط النموذج بعناية لتقليل الهلوسة:

- `temperature: 0.1` — إجابات حتمية وموثوقة
- `repeat_penalty: 1.1` — يمنع التكرار
- تعليمات صارمة في الـ System Prompt تمنع إضافة محتوى غير موجود في النص الأصلي
- النموذج مُوجَّه لإخراج الترجمة/الملخص **فقط** بدون مقدمات أو تعليقات

---

## 🐛 استكشاف الأخطاء

```bash
# عرض سجلات الحاوية
docker compose logs -f

# إعادة التشغيل
docker compose restart

# إيقاف كامل
docker compose down
```
