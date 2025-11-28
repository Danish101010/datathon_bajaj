# Testing Checklist - Before Deployment

## Prerequisites ✓

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Poppler installed (for PDF processing)
- [ ] Gemini API key obtained and set

## Environment Setup ✓

### 1. Set API Key

**Quick Setup (PowerShell):**
```powershell
.\setup_api_key.ps1
```

**Or Manual:**
```powershell
$env:GEMINI_API_KEY="your-key-here"
```

**Verify:**
```powershell
echo $env:GEMINI_API_KEY
```

### 2. Verify Dependencies

```bash
python -c "import google.generativeai; print('Gemini SDK: OK')"
python -c "import cv2; print('OpenCV: OK')"
python -c "from pdf2image import convert_from_path; print('pdf2image: OK')"
python -c "import fastapi; print('FastAPI: OK')"
```

## Local Testing ✓

### Test 1: Direct Gemini Connection

```bash
python test_gemini.py
```

**Expected Output:**
```
Available Gemini Models:
  - models/gemini-1.5-pro
✓ Gemini API connection successful!
```

### Test 2: Start API Server

```bash
python api.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test 3: Health Check

**New Terminal:**
```bash
curl http://localhost:8000/
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "Medical Bill Extraction API",
  "version": "1.0.0"
}
```

### Test 4: API Documentation

Open in browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Verify:**
- [ ] `/extract-bill-data` endpoint is visible
- [ ] Request schema shows `document` field
- [ ] Response schema matches hackathon format

### Test 5: Sample Image Extraction (sample_3.png)

```bash
python test_gemini.py
```

**Or using curl:**
```bash
curl -X POST http://localhost:8000/extract-bill-data ^
  -H "Content-Type: application/json" ^
  -d "{\"document\": \"https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_3.png?sv=2025-07-05&spr=https&st=2025-11-24T14:24:39Z&se=2026-11-25T14:24:00Z&sr=b&sp=r&sig=egKAmIUms8H5f3kgrGXKvcfuBVlQp0Qc2tsfxdvRgUY=3D\"}"
```

**Verify Response:**
- [ ] `is_success: true`
- [ ] `token_usage` has values > 0
- [ ] `data.pagewise_line_items` is array
- [ ] Each item has: `item_name`, `item_amount`, `item_rate`, `item_quantity`
- [ ] `data.total_item_count` matches actual count
- [ ] All amounts are floats with 2 decimals
- [ ] Page numbers are strings

### Test 6: Test All Sample Images

Download training samples:
```bash
curl -o training_samples.zip "https://hackrx.blob.core.windows.net/files/TRAINING_SAMPLES.zip?sv=2025-07-05&spr=https&st=2025-11-28T06:47:35Z&se=2025-11-29T06:47:35Z&sr=b&sp=r&sig=yB8R2zjoRL2%2FWRuv7E1lvmWSHAkm%2FoIGsepj2Io9pak%3D"
Expand-Archive training_samples.zip
```

Test each sample:
```python
import requests
import os

samples = [f for f in os.listdir('training_samples') if f.endswith(('.png', '.jpg', '.pdf'))]

for sample in samples:
    print(f"Testing {sample}...")
    # Upload file and test
```

## Validation Checklist ✓

### Response Format Validation

- [ ] Response is valid JSON
- [ ] `is_success` is boolean
- [ ] `token_usage.total_tokens` is integer >= 0
- [ ] `token_usage.input_tokens` is integer >= 0
- [ ] `token_usage.output_tokens` is integer >= 0
- [ ] `data` object exists
- [ ] `data.pagewise_line_items` is array
- [ ] `data.total_item_count` is integer >= 0

### Item Validation

For each item in `bill_items`:
- [ ] `item_name` is non-empty string
- [ ] `item_amount` is float or null
- [ ] `item_rate` is float or null
- [ ] `item_quantity` is float or null
- [ ] Floats have exactly 2 decimal places

### Business Logic Validation

- [ ] No duplicate items (same name + amount)
- [ ] `total_item_count` equals unique items after deduplication
- [ ] Sum of all `item_amount` is reasonable
- [ ] Item names match exactly as printed in bill
- [ ] No hallucinated items (verify against actual bill)

## Performance Testing ✓

### Response Time

- [ ] Single page < 30 seconds
- [ ] Multi-page (5 pages) < 2 minutes
- [ ] Large PDF (10+ pages) < 5 minutes

### Token Usage

Typical ranges:
- Simple bill (1 page): 3,000-6,000 input tokens
- Complex bill (5 pages): 15,000-30,000 input tokens
- Output: 200-500 tokens per page

### Accuracy Testing

For each test document:
1. Extract using API
2. Manually count items in original bill
3. Manually sum all amounts
4. Compare:
   - [ ] Item count matches
   - [ ] Total amount within 1% of actual
   - [ ] No missing items
   - [ ] No duplicate items
   - [ ] Item names exact match

## Error Handling ✓

### Test Error Cases

1. **Invalid URL:**
```bash
curl -X POST http://localhost:8000/extract-bill-data \
  -H "Content-Type: application/json" \
  -d '{"document": "invalid-url"}'
```
- [ ] Returns error response
- [ ] `is_success: false`
- [ ] Contains error message

2. **Missing document field:**
```bash
curl -X POST http://localhost:8000/extract-bill-data \
  -H "Content-Type: application/json" \
  -d '{}'
```
- [ ] Returns 422 validation error

3. **Network timeout:**
- [ ] API handles timeouts gracefully
- [ ] Returns appropriate error message

4. **Invalid API key:**
```bash
$env:GEMINI_API_KEY="invalid"
python api.py
```
- [ ] Returns clear error message

## Pre-Deployment Checklist ✓

### Code Quality

- [ ] No hardcoded API keys in code
- [ ] All sensitive data in environment variables
- [ ] Error handling for all external calls
- [ ] Logging for debugging
- [ ] Type hints on all functions
- [ ] Docstrings for main functions

### Files Ready

- [ ] `api.py` - Main API file
- [ ] `image_pipeline.py` - Image processing
- [ ] `extraction_prompts.py` - LLM prompts
- [ ] `reconciliation.py` - Data reconciliation
- [ ] `requirements.txt` - Dependencies
- [ ] `Procfile` - Deployment command
- [ ] `runtime.txt` - Python version
- [ ] `render.yaml` - Render config
- [ ] `Dockerfile` - Docker config
- [ ] `.gitignore` - Git ignore patterns
- [ ] `README.md` - Documentation
- [ ] `DEPLOYMENT.md` - Deployment guide

### Git Repository

- [ ] All files committed
- [ ] No sensitive data in repo
- [ ] `.gitignore` configured
- [ ] README.md complete
- [ ] Repository is public (or accessible to evaluators)

### Documentation

- [ ] README explains the approach
- [ ] Setup instructions clear
- [ ] API endpoints documented
- [ ] Example requests/responses provided
- [ ] Known limitations mentioned

## Final Verification ✓

### Before Submission

1. **Clean restart test:**
   - [ ] Fresh terminal
   - [ ] Set API key
   - [ ] Start API
   - [ ] Test sample_3.png
   - [ ] Verify response format

2. **Postman collection:**
   - [ ] Import provided Postman collection
   - [ ] Update base URL to your deployment
   - [ ] Test all endpoints
   - [ ] Verify responses match schema

3. **Deployment test:**
   - [ ] Deploy to Render
   - [ ] Set environment variables
   - [ ] Test deployed API
   - [ ] Verify public access
   - [ ] Test with Postman

4. **Documentation review:**
   - [ ] README is complete
   - [ ] All steps tested and working
   - [ ] Known issues documented
   - [ ] Contact info provided

## Troubleshooting

### Common Issues and Fixes

| Issue | Fix |
|-------|-----|
| "GEMINI_API_KEY not set" | Run `setup_api_key.ps1` or set manually |
| "Module not found" | `pip install -r requirements.txt --force-reinstall` |
| "Poppler not found" | Install poppler-utils and add to PATH |
| "Port 8000 in use" | Change port or kill process |
| "Request timeout" | Increase timeout, check network |
| "Invalid response format" | Check Gemini response in logs |
| "Wrong token count" | Verify using `response.usage_metadata` |

## Success Criteria ✓

Your API is ready when:

- [✓] All tests pass
- [✓] Sample images extract correctly
- [✓] Response format matches hackathon schema exactly
- [✓] No missing or duplicate items
- [✓] Total amounts within 1% of actual
- [✓] Deployed and publicly accessible
- [✓] Documentation complete
- [✓] Repository submitted

---

**Last Updated:** {current_date}
**Status:** Ready for Deployment ✓
