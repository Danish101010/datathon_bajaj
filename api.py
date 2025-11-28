import os
import tempfile
import json
import base64
from typing import List, Dict, Optional
from pathlib import Path
import traceback

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from image_pipeline import process_document, preprocess_image, pdf_to_images
from extraction_prompts import create_extraction_prompt, validate_extraction_response
from reconciliation import reconcile_extractions, validate_reconciliation_output


app = FastAPI(
    title="Medical Bill Extraction API",
    description="Extract line items from medical/pharmacy bills using multimodal AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractionRequest(BaseModel):
    document: str = Field(..., description="URL to download document from")





import google.generativeai as genai
from PIL import Image as PILImage

def send_gemini_multimodal(
    system_prompt: str,
    user_prompt: str,
    images: List[str],
    temperature: float = 0.0
) -> Dict:
    """
    Send multimodal request to Gemini API.
    
    Args:
        system_prompt: System instructions
        user_prompt: User prompt with extraction instructions
        images: List of image file paths
        temperature: Generation temperature
    
    Returns:
        Dictionary with extracted data and token usage
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Load images using PIL
    image_parts = []
    for img_path in images:
        try:
            pil_image = PILImage.open(img_path)
            image_parts.append(pil_image)
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            continue
    
    if not image_parts:
        raise ValueError("No valid images loaded")
    
    # Combine prompts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    # Create content parts
    content_parts = [full_prompt] + image_parts
    
    # Generate response
    response = model.generate_content(
        content_parts,
        generation_config={
            'temperature': temperature,
            'top_p': 1.0,
            'top_k': 32,
            'max_output_tokens': 4096,
        }
    )
    
    # Extract JSON from response
    response_text = response.text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    elif response_text.startswith('```'):
        response_text = response_text[3:]
    
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    
    response_text = response_text.strip()
    
    try:
        extracted_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Response text: {response_text[:500]}")
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
    
    # Get token usage
    token_usage = {
        'input_tokens': 0,
        'output_tokens': 0,
        'total_tokens': 0
    }
    
    if hasattr(response, 'usage_metadata') and response.usage_metadata:
        token_usage = {
            'input_tokens': response.usage_metadata.prompt_token_count,
            'output_tokens': response.usage_metadata.candidates_token_count,
            'total_tokens': response.usage_metadata.total_token_count
        }
    
    return {
        'extracted_data': extracted_data,
        'token_usage': token_usage
    }
   

def extract_page_with_gemini(page_meta: Dict, page_type_hint: str) -> Dict:
    """
    Extract bill items from a single page using Gemini.
    
    Args:
        page_meta: Page metadata from image pipeline
        page_type_hint: Hint about page type
    
    Returns:
        Extracted page data
    """
    page_no = str(page_meta['page_no'])
    full_image_path = page_meta['full_image_path']
    
    region_images = []
    image_paths = [full_image_path]
    
    for crop in page_meta['crops'][1:11]:
        region_images.append({
            "crop_id": crop['crop_id'],
            "bbox": crop['bbox'],
            "image": f"<crop_{crop['crop_id']}>"
        })
        image_paths.append(crop['path'])
    
    prompt_data = create_extraction_prompt(
        page_no=page_no,
        page_type_hint=page_type_hint,
        full_page_image_ref="<full_page_image>",
        region_images=region_images
    )
    
    try:
        print(f"Extracting page {page_no}...")
        print(f"Sending {len(image_paths)} images to Gemini")
        
        gemini_response = send_gemini_multimodal(
            system_prompt=prompt_data['system_prompt'],
            user_prompt=prompt_data['user_prompt'],
            images=image_paths,
            temperature=0.0
        )
        
        extracted_data = gemini_response.get('extracted_data', {})
        token_usage = gemini_response.get('token_usage', {
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0
        })
        
        print(f"Page {page_no}: Extracted {len(extracted_data.get('bill_items', []))} items")
        
        if not validate_extraction_response(extracted_data):
            print(f"Page {page_no}: Validation failed")
            return {
                'page_no': page_no,
                'page_type': 'Other',
                'bill_items': [],
                'error': 'Invalid response format',
                'token_usage': token_usage
            }
        
        extracted_data['token_usage'] = token_usage
        return extracted_data
        
    except ValueError as e:
        error_msg = str(e)
        print(f"Page {page_no}: ValueError - {error_msg}")
        return {
            'page_no': page_no,
            'page_type': 'Other',
            'bill_items': [],
            'error': error_msg,
            'token_usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        }
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"Page {page_no}: Exception - {error_msg}")
        traceback.print_exc()
        return {
            'page_no': page_no,
            'page_type': 'Other',
            'bill_items': [],
            'error': error_msg,
            'token_usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        }


def cleanup_temp_files(temp_dir: str):
    """Clean up temporary files in background."""
    try:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception:
        pass


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Medical Bill Extraction API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "gemini_configured": False,
        "timestamp": None
    }


@app.post("/extract-bill-data")
async def extract_bill_data(
    background_tasks: BackgroundTasks,
    request: ExtractionRequest
):
    """
    Extract line items from medical/pharmacy bill.
    
    Request Body:
    {
        "document": "https://example.com/bill.pdf"
    }
    
    Response matches exact hackathon schema.
    """
    document_url = request.document
    
    temp_dir = tempfile.mkdtemp()
    background_tasks.add_task(cleanup_temp_files, temp_dir)
    
    try:
        pages_metadata = process_document(document_url, temp_dir)
        
        extracted_pages = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        
        for page_meta in pages_metadata:
            page_type_hint = "Bill Detail | Final Bill | Pharmacy"
            page_result = extract_page_with_gemini(page_meta, page_type_hint)
            
            token_usage = page_result.pop('token_usage', {})
            total_input_tokens += token_usage.get('input_tokens', 0)
            total_output_tokens += token_usage.get('output_tokens', 0)
            total_tokens += token_usage.get('total_tokens', 0)
            
            extracted_pages.append(page_result)
        
        reconciliation_input = {
            "pages": extracted_pages,
            "printed_totals_images": []
        }
        
        final_output = reconcile_extractions(reconciliation_input)
        
        final_output['token_usage'] = {
            'input_tokens': total_input_tokens,
            'output_tokens': total_output_tokens,
            'total_tokens': total_tokens
        }
        
        if not validate_reconciliation_output(final_output):
            raise HTTPException(status_code=500, detail="Invalid output format generated")
        
        return JSONResponse(content=final_output)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        return JSONResponse(
            status_code=500,
            content={
                "is_success": False,
                "token_usage": {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
                "data": {"pagewise_line_items": [], "total_item_count": 0},
                "error": f"{str(e)}\n\n{error_trace}"
            }
        )





if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1
    )
