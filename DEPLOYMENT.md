# Local Testing & Deployment Guide

## Local Testing

### Prerequisites

1. **Install Python 3.11+**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Install Poppler (for PDF processing)**
   - **Windows**: Download from https://github.com/oschwartz10612/poppler-windows/releases/
     - Extract and add `bin` folder to PATH
     - Or use: `choco install poppler` (if using Chocolatey)
   - **Linux**: `sudo apt-get install poppler-utils`
   - **macOS**: `brew install poppler`

3. **Verify Poppler Installation**
   ```bash
   pdftoppm -h  # Should show help text
   ```

### Setup Local Environment

1. **Create Virtual Environment**
   ```bash
   cd c:\Users\mohdd\Downloads\datatho_gemini
   python -m venv venv
   ```

2. **Activate Virtual Environment**
   ```bash
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   
   # Windows CMD
   .\venv\Scripts\activate.bat
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Configure Gemini API (Optional for Testing)

1. **Get Gemini API Key**
   - Go to https://makersuite.google.com/app/apikey
   - Create new API key

2. **Set Environment Variable**
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your-api-key-here"
   
   # Windows CMD
   set GEMINI_API_KEY=your-api-key-here
   
   # Linux/macOS
   export GEMINI_API_KEY=your-api-key-here
   ```

3. **Implement Gemini Integration** (Edit `api.py`)
   ```python
   # Replace the send_gemini_multimodal function in api.py with:
   
   import google.generativeai as genai
   
   def send_gemini_multimodal(
       system_prompt: str,
       user_prompt: str,
       images: List[str],
       temperature: float = 0.0
   ) -> Dict:
       genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
       model = genai.GenerativeModel('gemini-1.5-pro')
       
       image_parts = []
       for img_path in images:
           with open(img_path, 'rb') as f:
               img_data = f.read()
               image_parts.append({
                   'mime_type': 'image/png',
                   'data': img_data
               })
       
       contents = [{
           'role': 'user',
           'parts': [
               {'text': system_prompt + "\n\n" + user_prompt},
               *image_parts
           ]
       }]
       
       response = model.generate_content(
           contents,
           generation_config={'temperature': temperature}
       )
       
       extracted_data = json.loads(response.text)
       
       return {
           'extracted_data': extracted_data,
           'token_usage': {
               'input_tokens': response.usage_metadata.prompt_token_count,
               'output_tokens': response.usage_metadata.candidates_token_count,
               'total_tokens': response.usage_metadata.total_token_count
           }
       }
   ```

### Run API Server Locally

```bash
# Start server
python api.py

# Or with uvicorn directly
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: **http://localhost:8000**

### Test Endpoints

1. **Health Check**
   ```bash
   curl http://localhost:8000/
   ```

2. **Test with File Upload**
   ```bash
   curl -X POST http://localhost:8000/extract \
     -F "file=@sample_bill.pdf" \
     -F "page_type_hint=Pharmacy"
   ```

3. **Test with URL**
   ```bash
   curl -X POST http://localhost:8000/extract \
     -d "document_url=https://example.com/bill.pdf" \
     -d "page_type_hint=Pharmacy"
   ```

4. **Interactive API Docs**
   - Open browser: http://localhost:8000/docs
   - Test endpoints interactively with Swagger UI

### Test with Python

```python
import requests

# Test file upload
with open('sample_bill.pdf', 'rb') as f:
    files = {'file': f}
    data = {'page_type_hint': 'Pharmacy'}
    response = requests.post('http://localhost:8000/extract', files=files, data=data)
    print(response.json())

# Test URL extraction
data = {
    'document_url': 'https://example.com/bill.pdf',
    'page_type_hint': 'Pharmacy'
}
response = requests.post('http://localhost:8000/extract-url', json=data)
print(response.json())
```

---

## Deployment to Render

### Prerequisites

1. **GitHub Account** (to connect repository)
2. **Render Account** (free at https://render.com)

### Step 1: Prepare Repository

1. **Initialize Git**
   ```bash
   cd c:\Users\mohdd\Downloads\datatho_gemini
   git init
   git add .
   git commit -m "Initial commit - Medical Bill Extraction API"
   ```

2. **Create GitHub Repository**
   - Go to https://github.com/new
   - Create new repository (e.g., `medical-bill-extraction`)
   - Don't initialize with README

3. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/medical-bill-extraction.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render

1. **Login to Render**
   - Go to https://dashboard.render.com/
   - Sign up/Login

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `medical-bill-extraction` repository

3. **Configure Service**
   ```
   Name: medical-bill-extraction
   Region: Choose closest to your users
   Branch: main
   Root Directory: (leave blank)
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
   ```

4. **Set Environment Variables**
   - Click "Environment" tab
   - Add variable:
     ```
     Key: GEMINI_API_KEY
     Value: your-gemini-api-key
     ```

5. **Install System Dependencies**
   - Render needs poppler for PDF processing
   - Add `render.yaml` configuration file:

### Step 3: Add render.yaml

Create `render.yaml` in project root:

```yaml
services:
  - type: web
    name: medical-bill-extraction
    runtime: python
    plan: free
    buildCommand: |
      apt-get update
      apt-get install -y poppler-utils
      pip install -r requirements.txt
    startCommand: uvicorn api:app --host 0.0.0.0 --port $PORT --workers 1
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: GEMINI_API_KEY
        sync: false
    autoDeploy: true
```

### Step 4: Deploy

1. **Push render.yaml to GitHub**
   ```bash
   git add render.yaml
   git commit -m "Add Render configuration"
   git push
   ```

2. **Trigger Deploy on Render**
   - Render will auto-detect the push
   - Build process will start automatically
   - Monitor logs in Render dashboard

3. **Wait for Deployment**
   - Build typically takes 5-10 minutes
   - Watch logs for any errors
   - Once complete, you'll get a URL like: `https://medical-bill-extraction.onrender.com`

### Step 5: Test Deployment

```bash
# Health check
curl https://your-app.onrender.com/

# Test extraction
curl -X POST https://your-app.onrender.com/extract-url \
  -H "Content-Type: application/json" \
  -d '{"document_url": "https://example.com/bill.pdf", "page_type_hint": "Pharmacy"}'
```

---

## Alternative Deployment: Docker

If you prefer Docker deployment:

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run

```bash
# Build image
docker build -t medical-bill-api .

# Run container
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key medical-bill-api
```

### Deploy to Render with Docker

1. Add `Dockerfile` to repository
2. In Render, select "Docker" as runtime
3. Render will auto-detect and use Dockerfile

---

## Troubleshooting

### Common Issues

1. **Poppler Not Found**
   ```
   Error: Unable to get page count. Is poppler installed and in PATH?
   ```
   **Solution**: Install poppler-utils (see prerequisites)

2. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'cv2'
   ```
   **Solution**: Reinstall requirements
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

3. **Render Build Fails**
   - Check logs in Render dashboard
   - Ensure `render.yaml` includes poppler installation
   - Verify all files are committed to Git

4. **API Returns Mock Data**
   - Gemini API not implemented
   - Set `GEMINI_API_KEY` environment variable
   - Implement `send_gemini_multimodal()` function

### Logs

**Local:**
```bash
# Run with debug logging
uvicorn api:app --reload --log-level debug
```

**Render:**
- View logs in Render dashboard
- Go to your service → "Logs" tab

---

## Performance Optimization

### For Production

1. **Increase Workers**
   ```bash
   uvicorn api:app --workers 4
   ```

2. **Add Caching**
   - Cache processed images
   - Use Redis for session storage

3. **Rate Limiting**
   ```bash
   pip install slowapi
   ```

4. **Upgrade Render Plan**
   - Free tier has limitations
   - Upgrade for better performance

---

## API Documentation

Once deployed, interactive docs available at:
- Swagger UI: `https://your-app.onrender.com/docs`
- ReDoc: `https://your-app.onrender.com/redoc`

---

## Support

For issues:
1. Check logs first
2. Verify environment variables
3. Test locally before deploying
4. Review Render build logs

## Costs

- **Render Free Tier**: Limited to 750 hours/month, sleeps after inactivity
- **Gemini API**: Pay-per-use (check Google AI Studio pricing)
- **Render Paid**: ~$7/month for always-on service
