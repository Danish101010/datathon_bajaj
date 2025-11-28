import os
import requests
import json
from pathlib import Path


def test_gemini_extraction():
    """Test Gemini extraction with the provided sample image."""
    
    # Check if API key is set
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set!")
        print("\nTo set it:")
        print("  PowerShell: $env:GEMINI_API_KEY='your-key-here'")
        print("  CMD: set GEMINI_API_KEY=your-key-here")
        return
    
    print("✓ GEMINI_API_KEY is set")
    print(f"  Key preview: {api_key[:10]}...{api_key[-10:]}")
    
    # Test URL from hackathon
    test_url = "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_3.png?sv=2025-07-05&spr=https&st=2025-11-24T14%3A24%3A39Z&se=2026-11-25T14%3A24%3A00Z&sr=b&sp=r&sig=egKAmIUms8H5f3kgrGXKvcfuBVlQp0Qc2tsfxdvRgUY%3D"
    
    print(f"\n{'='*70}")
    print("Testing Gemini Extraction Pipeline")
    print(f"{'='*70}")
    print(f"\nTest Image: sample_3.png")
    print(f"URL: {test_url[:80]}...")
    
    # API endpoint
    api_url = "http://localhost:8000/extract-bill-data"
    
    print(f"\n{'='*70}")
    print("Sending request to API...")
    print(f"{'='*70}")
    
    # Request payload
    payload = {
        "document": test_url
    }
    
    try:
        # Make request
        response = requests.post(
            api_url,
            json=payload,
            timeout=180  # 3 minutes timeout for processing
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n{'='*70}")
            print("EXTRACTION RESULTS")
            print(f"{'='*70}")
            
            # Basic info
            print(f"\nSuccess: {result.get('is_success')}")
            
            # Token usage
            token_usage = result.get('token_usage', {})
            print(f"\nToken Usage:")
            print(f"  Input Tokens:  {token_usage.get('input_tokens', 0):,}")
            print(f"  Output Tokens: {token_usage.get('output_tokens', 0):,}")
            print(f"  Total Tokens:  {token_usage.get('total_tokens', 0):,}")
            
            # Data
            data = result.get('data', {})
            total_items = data.get('total_item_count', 0)
            pagewise_items = data.get('pagewise_line_items', [])
            
            print(f"\nTotal Unique Items: {total_items}")
            print(f"Number of Pages: {len(pagewise_items)}")
            
            # Page-wise breakdown
            print(f"\n{'='*70}")
            print("PAGE-WISE BREAKDOWN")
            print(f"{'='*70}")
            
            total_amount = 0.0
            
            for page in pagewise_items:
                page_no = page.get('page_no')
                page_type = page.get('page_type')
                bill_items = page.get('bill_items', [])
                
                print(f"\nPage {page_no} ({page_type})")
                print(f"  Items: {len(bill_items)}")
                
                page_total = 0.0
                for idx, item in enumerate(bill_items, 1):
                    item_name = item.get('item_name', 'N/A')
                    item_amount = item.get('item_amount')
                    item_rate = item.get('item_rate')
                    item_quantity = item.get('item_quantity')
                    
                    # Format values
                    amount_str = f"₹{item_amount:.2f}" if item_amount is not None else "N/A"
                    rate_str = f"₹{item_rate:.2f}" if item_rate is not None else "N/A"
                    qty_str = f"{item_quantity:.2f}" if item_quantity is not None else "N/A"
                    
                    print(f"  {idx}. {item_name}")
                    print(f"     Qty: {qty_str} | Rate: {rate_str} | Amount: {amount_str}")
                    
                    if item_amount is not None:
                        page_total += item_amount
                        total_amount += item_amount
                
                print(f"  Page Total: ₹{page_total:.2f}")
            
            print(f"\n{'='*70}")
            print(f"TOTAL BILL AMOUNT: ₹{total_amount:.2f}")
            print(f"{'='*70}")
            
            # Save response to file
            output_file = "test_response.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Full response saved to: {output_file}")
            
        else:
            print(f"\nERROR: Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
    
    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out (>180 seconds)")
        print("This might happen with complex documents or slow network")
    
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to API server")
        print("Make sure the API is running:")
        print("  python api.py")
    
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


def test_direct_gemini():
    """Test Gemini API directly without the full pipeline."""
    print(f"\n{'='*70}")
    print("Testing Direct Gemini API Connection")
    print(f"{'='*70}")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        return
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        
        # List available models
        print("\nAvailable Gemini Models:")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"  - {model.name}")
        
        # Simple test
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Say 'Gemini API is working!'")
        
        print(f"\nTest Response: {response.text}")
        print("✓ Gemini API connection successful!")
        
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Medical Bill Extraction - Gemini Integration Test")
    print("=" * 70)
    
    # Test direct Gemini connection first
    test_direct_gemini()
    
    print("\n" + "=" * 70)
    input("Press Enter to test full extraction pipeline...")
    
    # Test full pipeline
    test_gemini_extraction()
