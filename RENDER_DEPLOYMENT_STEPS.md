# Step-by-Step Render Deployment Guide

## ✅ Prerequisites Complete
- API is working locally ✓
- Gemini extraction successful ✓
- Test extracted 12 items, ₹16,390.00 total ✓

## Step 1: Prepare Git Repository (5 minutes)

### 1.1 Initialize Git (if not done)
```powershell
cd C:\Users\mohdd\Downloads\datatho_gemini
git init
```

### 1.2 Create .gitignore (already exists)
Verify it contains:
```
__pycache__/
*.pyc
venv/
.env
*.pdf
*.png
*.jpg
processed/
```

### 1.3 Commit all files
```powershell
git add .
git commit -m "Medical bill extraction API - HackRx submission"
```

## Step 2: Create GitHub Repository (3 minutes)

### 2.1 Go to GitHub
- Open: https://github.com/new
- Sign in if needed

### 2.2 Create Repository
- **Repository name:** `medical-bill-extraction` (or your preferred name)
- **Description:** `AI-powered medical bill extraction API for HackRx Datathon`
- **Visibility:** Public (required for free Render deployment)
- **Do NOT** initialize with README (we already have files)
- Click **Create repository**

### 2.3 Push to GitHub
Copy the commands from GitHub (under "...or push an existing repository"):
```powershell
git remote add origin https://github.com/YOUR_USERNAME/medical-bill-extraction.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

**Verify:** Refresh GitHub page - you should see all your files!

## Step 3: Sign Up for Render (2 minutes)

### 3.1 Go to Render
- Open: https://render.com
- Click **Get Started** or **Sign Up**

### 3.2 Sign Up Options
- **Recommended:** Sign up with GitHub (easiest)
- Or use email/Google

### 3.3 Connect GitHub
- If not using GitHub signup, go to Account Settings → Connect GitHub
- Authorize Render to access your repositories

## Step 4: Create Web Service (5 minutes)

### 4.1 Create New Web Service
- From Render Dashboard, click **New +**
- Select **Web Service**

### 4.2 Connect Repository
- You'll see list of your GitHub repositories
- Find and select: `medical-bill-extraction`
- Click **Connect**

### 4.3 Configure Service

**Basic Settings:**
```
Name: medical-bill-extraction
Region: Singapore (or closest to you)
Branch: main
Root Directory: (leave blank)
Runtime: Python 3
```

**Build & Deploy:**
```
Build Command: pip install -r requirements.txt
Start Command: uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Instance Type:**
```
Free (or Starter if you want better performance)
```

### 4.4 Advanced Settings (IMPORTANT!)

Click **Advanced** button

**Add Environment Variable:**
```
Key: GEMINI_API_KEY
Value: [paste your actual API key here]
```

**Add Build Command (for system dependencies):**

In the **Build Command** field, replace with:
```bash
apt-get update && apt-get install -y poppler-utils libgl1-mesa-glx libglib2.0-0 && pip install -r requirements.txt
```

Or better yet, Render will auto-detect `render.yaml` (already in your repo)!

## Step 5: Deploy! (10-15 minutes)

### 5.1 Start Deployment
- Click **Create Web Service**
- Deployment will start automatically

### 5.2 Monitor Build Logs
You'll see logs like:
```
==> Cloning from https://github.com/YOUR_USERNAME/medical-bill-extraction...
==> Downloading cache...
==> Installing dependencies from requirements.txt
==> Running build command
==> Starting service with uvicorn...
==> Your service is live 🎉
```

**Build takes 10-15 minutes** (be patient!)

### 5.3 Watch for Errors
Common issues:
- ✅ Poppler installation - should work with render.yaml
- ✅ Python version - runtime.txt specifies 3.11
- ✅ Dependencies - requirements.txt has everything

## Step 6: Test Deployed API (3 minutes)

### 6.1 Get Your URL
Once deployed, you'll see:
```
Your service is live at https://medical-bill-extraction.onrender.com
```

Copy this URL!

### 6.2 Test Health Endpoint
```powershell
curl https://medical-bill-extraction.onrender.com/
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Medical Bill Extraction API",
  "version": "1.0.0"
}
```

### 6.3 Test Extraction
```powershell
curl -X POST https://medical-bill-extraction.onrender.com/extract-bill-data `
  -H "Content-Type: application/json" `
  -d '{\"document\": \"https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_3.png?sv=2025-07-05&spr=https&st=2025-11-24T14:24:39Z&se=2026-11-25T14:24:00Z&sr=b&sp=r&sig=egKAmIUms8H5f3kgrGXKvcfuBVlQp0Qc2tsfxdvRgUY%3D\"}'
```

Should return the same extraction result!

### 6.4 Open API Docs
```
https://medical-bill-extraction.onrender.com/docs
```

Interactive Swagger UI will open!

## Step 7: Important Settings (2 minutes)

### 7.1 Auto-Deploy (Optional)
- Go to your service → Settings
- **Auto-Deploy:** Enabled (already on by default)
- Every git push will trigger new deployment

### 7.2 Health Check
- Settings → Health Check Path: `/health`
- This helps Render monitor your service

### 7.3 Environment Variables
- Settings → Environment
- Verify `GEMINI_API_KEY` is set (hidden for security)

## Step 8: Update README for Submission (5 minutes)

### 8.1 Add Deployment URL to README
Edit your README.md and add:

```markdown
## 🚀 Live Demo

**API Endpoint:** https://medical-bill-extraction.onrender.com

**API Documentation:** https://medical-bill-extraction.onrender.com/docs

### Test the API:

```bash
curl -X POST https://medical-bill-extraction.onrender.com/extract-bill-data \
  -H "Content-Type: application/json" \
  -d '{"document": "YOUR_IMAGE_URL_HERE"}'
```
```

### 8.2 Commit and Push
```powershell
git add README.md
git commit -m "Add deployment URL"
git push
```

Render will auto-deploy the update!

## Step 9: Final Verification Checklist ✓

### Test All Endpoints:

#### 1. Health Check
```bash
curl https://YOUR-APP.onrender.com/
```
✅ Should return: `{"status": "healthy"}`

#### 2. API Docs
```
https://YOUR-APP.onrender.com/docs
```
✅ Should show Swagger UI

#### 3. Extract Sample Image
```bash
curl -X POST https://YOUR-APP.onrender.com/extract-bill-data \
  -H "Content-Type: application/json" \
  -d '{"document": "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_3.png?sv=2025-07-05&spr=https&st=2025-11-24T14:24:39Z&se=2026-11-25T14:24:00Z&sr=b&sp=r&sig=egKAmIUms8H5f3kgrGXKvcfuBVlQp0Qc2tsfxdvRgUY%3D"}'
```
✅ Should return JSON with extracted items

#### 4. Verify Response Schema
Check response has:
- ✅ `is_success: true`
- ✅ `token_usage` with counts
- ✅ `data.pagewise_line_items` array
- ✅ `data.total_item_count` integer
- ✅ All amounts as floats with 2 decimals

## Step 10: Submit to HackRx 🎉

### 10.1 Prepare Submission
You need to provide:
1. **GitHub Repository URL:** `https://github.com/YOUR_USERNAME/medical-bill-extraction`
2. **Deployed API URL:** `https://your-app.onrender.com`
3. **API Endpoint:** `https://your-app.onrender.com/extract-bill-data`

### 10.2 Test with Postman Collection
- Import the provided Postman collection
- Update base URL to your Render URL
- Test all sample images
- Verify response format matches exactly

### 10.3 Final README Check
Your README.md should include:
- ✅ Project description
- ✅ Approach explanation
- ✅ Architecture diagram/explanation
- ✅ Setup instructions
- ✅ Deployment URL
- ✅ API usage examples
- ✅ Tech stack details
- ✅ Known limitations

## Troubleshooting

### Build Fails

**"Poppler not found"**
```
Solution: render.yaml should handle this automatically
Verify: Check build logs for "apt-get install poppler-utils"
```

**"Module not found"**
```
Solution: Check requirements.txt is complete
Fix: Add missing package and push
```

### Deployment Succeeds But API Fails

**"GEMINI_API_KEY not set"**
```
Solution: Go to Render Dashboard → Your Service → Environment
Add: GEMINI_API_KEY with your actual key
Click "Save Changes" - service will redeploy
```

**"Import Error"**
```
Solution: Check Python version compatibility
Fix: Verify runtime.txt has python-3.11.0
```

### API Times Out

**Request takes too long**
```
Reason: Free tier has limited CPU
Solution: 
- Upgrade to Starter ($7/mo) for better performance
- Or reduce number of crops in api.py (line 157)
```

### Check Logs

**View Logs in Render:**
- Go to your service
- Click "Logs" tab
- See real-time logs
- Look for errors

**Download Logs:**
- Logs tab → Download
- Search for specific errors

## Performance Tips

### 1. Reduce Crops for Faster Processing
Edit `api.py` line 157:
```python
# Change from:
for crop in page_meta['crops'][1:11]:

# To (fewer crops, faster):
for crop in page_meta['crops'][1:5]:
```

### 2. Use Smaller Images
For PDFs, reduce DPI in `image_pipeline.py`:
```python
# Change from 300 to 200 DPI
images = convert_from_bytes(pdf_bytes, dpi=200)
```

### 3. Upgrade Render Plan
- Free tier: 512MB RAM, 0.1 CPU
- Starter ($7/mo): 512MB RAM, 0.5 CPU
- Better for production use

## Cost Estimation

### Render Costs:
- **Free Tier:** $0/month (750 hours, sleeps after 15min inactivity)
- **Starter:** $7/month (always on, better performance)

### Gemini API Costs:
- Input: ~$0.03 per 1000 images
- Output: ~$0.01 per 1000 responses
- **Estimated:** $0.04 per document

### For Hackathon:
- Use Free tier ✅
- Should handle evaluation traffic easily

## Next Steps After Deployment

1. ✅ Test with ALL provided sample images
2. ✅ Verify accuracy against actual bills
3. ✅ Document approach in README
4. ✅ Add error handling examples
5. ✅ Submit GitHub + Render URLs

## Quick Reference Commands

```powershell
# Check git status
git status

# Commit changes
git add .
git commit -m "Update message"
git push

# View logs locally
python api.py  # Watch terminal for logs

# Test locally
python test_gemini.py

# Test deployed API
curl https://YOUR-APP.onrender.com/
```

## Your Deployment URLs

After deployment, fill these in:

```
GitHub Repository: https://github.com/YOUR_USERNAME/medical-bill-extraction
Render Dashboard: https://dashboard.render.com/
Live API: https://YOUR-APP.onrender.com
API Docs: https://YOUR-APP.onrender.com/docs
```

---

## 🎯 You're Ready to Deploy!

Follow steps 1-10 above, and you'll have a working API deployed in ~30 minutes!

**Questions during deployment?** Check the Troubleshooting section above.

**Good luck with HackRx! 🚀**
