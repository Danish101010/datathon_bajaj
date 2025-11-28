# Quick Start Guide

## 🚀 Run API Locally (5 minutes)

### Step 1: Install Poppler

**Windows:**
```powershell
# Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
# Extract and add bin folder to PATH, or:
choco install poppler  # If you have Chocolatey
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Verify installation:**
```bash
pdftoppm -h  # Should show help text
```

### Step 2: Setup Python Environment

```bash
# Navigate to project
cd c:\Users\mohdd\Downloads\datatho_gemini

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Set Gemini API Key

**Get API Key:** https://makersuite.google.com/app/apikey

```powershell
# Windows PowerShell
$env:GEMINI_API_KEY="AIzaSy..."

# Or add to system environment variables permanently
```

### Step 4: Start Server

```bash
python api.py
```

**Server started at:** http://localhost:8000

### Step 5: Test API

**Option 1: Use test script**
```bash
python test_api.py
```

**Option 2: Use curl**
```bash
curl -X POST http://localhost:8000/extract-bill-data ^
  -H "Content-Type: application/json" ^
  -d "{\"document\": \"https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png\"}"
```

**Option 3: Use browser**
- Open: http://localhost:8000/docs
- Click "Try it out" on `/extract-bill-data`
- Enter document URL
- Click "Execute"

---

## 🌐 Deploy to Render (10 minutes)

### Step 1: Prepare Git Repository

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "HackRx Datathon submission"
```

### Step 2: Push to GitHub

```bash
# Create repo on GitHub: https://github.com/new

# Add remote
git remote add origin https://github.com/YOUR_USERNAME/medical-bill-extraction.git

# Push
git branch -M main
git push -u origin main
```

### Step 3: Deploy on Render

1. **Login to Render**: https://dashboard.render.com/
2. **Create Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select your repository
3. **Configure** (auto-filled from render.yaml):
   - Name: `medical-bill-extraction`
   - Runtime: Python 3
   - Build Command: (auto-detected)
   - Start Command: (auto-detected)
4. **Add Environment Variable**:
   - Click "Environment" tab
   - Add: `GEMINI_API_KEY` = `your-api-key`
5. **Deploy**:
   - Click "Create Web Service"
   - Wait 5-10 minutes for build

### Step 4: Test Deployed API

```bash
# Your live URL
https://medical-bill-extraction.onrender.com

# Test endpoint
curl -X POST https://medical-bill-extraction.onrender.com/extract-bill-data \
  -H "Content-Type: application/json" \
  -d '{"document": "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png"}'
```

---

## 🧪 Test with HackRx Training Data

### Download Training Samples

```bash
# Download training data
curl -o training.zip "https://hackrx.blob.core.windows.net/files/TRAINING_SAMPLES.zip?sv=..."

# Extract
unzip training.zip
```

### Test Each Document

```python
import requests
import os

base_url = "http://localhost:8000"  # or your Render URL

# Test all documents
for file in os.listdir("training_samples"):
    if file.endswith(('.pdf', '.png', '.jpg')):
        # Upload file or provide URL
        response = requests.post(
            f"{base_url}/extract-bill-data",
            json={"document": f"file://{file}"}  # or use URL
        )
        
        result = response.json()
        print(f"{file}: {result['data']['total_item_count']} items")
```

---

## 📊 Verify Results

### Check Accuracy

1. **Item Count**: Should match visual count
2. **Total Amount**: AI total ≈ Printed total
3. **No Duplicates**: Same item should appear once
4. **All Items**: No missed line items

### Expected Output Format

```json
{
  "is_success": true,
  "token_usage": {"total_tokens": 1234, "input_tokens": 800, "output_tokens": 434},
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Pharmacy",
        "bill_items": [
          {"item_name": "Item 1", "item_amount": 100.00, "item_rate": 50.00, "item_quantity": 2.00}
        ]
      }
    ],
    "total_item_count": 1
  }
}
```

---

## ❓ Troubleshooting

### Issue: "poppler not found"
```bash
# Install poppler (see Step 1)
# Add to PATH or verify installation
pdftoppm -h
```

### Issue: "Gemini API error"
```bash
# Check API key is set
echo $env:GEMINI_API_KEY

# Get new key at: https://makersuite.google.com/app/apikey
```

### Issue: "ModuleNotFoundError"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: "Render build fails"
- Check build logs in Render dashboard
- Verify `render.yaml` is committed to Git
- Ensure `GEMINI_API_KEY` is set in Render environment

---

## 📝 Submission Checklist

- [ ] API runs locally (`python api.py`)
- [ ] Test script passes (`python test_api.py`)
- [ ] API deployed to Render
- [ ] GitHub repository created
- [ ] README.md is complete
- [ ] Environment variables set
- [ ] Test with training data
- [ ] Verify output schema matches spec

---

## 🎯 Next Steps

1. **Test thoroughly** with training data
2. **Optimize** prompts for accuracy
3. **Monitor** token usage
4. **Submit** GitHub repo URL
5. **Document** your approach in README

---

**Need Help?**
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guides
- Review API docs at `/docs` endpoint
- Test locally before deploying

**Good luck with HackRx! 🚀**
