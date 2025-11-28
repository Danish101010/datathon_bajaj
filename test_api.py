import requests
import json


BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_extract_bill_data(url: str):
    """Test /extract-bill-data endpoint (hackathon spec)."""
    print(f"Testing /extract-bill-data: {url}")
    
    try:
        payload = {
            'document': url
        }
        
        response = requests.post(
            f"{BASE_URL}/extract-bill-data",
            json=payload,
            timeout=120
        )
        
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Success: {result.get('is_success')}")
        print(f"Total Items: {result.get('data', {}).get('total_item_count', 0)}")
        print(f"Pages: {len(result.get('data', {}).get('pagewise_line_items', []))}")
        
        if result.get('is_success'):
            print("\nExtracted Bill Items:")
            for page in result.get('data', {}).get('pagewise_line_items', []):
                print(f"\n  Page {page['page_no']} ({page['page_type']}):")
                for item in page['bill_items'][:3]:
                    print(f"    - {item['item_name']}: ₹{item['item_amount']}")
        
        print(f"\nFull Response: {json.dumps(result, indent=2)}\n")
        
    except Exception as e:
        print(f"Error: {e}\n")


def test_api_docs():
    """Test API documentation endpoint."""
    print("API Documentation available at:")
    print(f"  Swagger UI: {BASE_URL}/docs")
    print(f"  ReDoc: {BASE_URL}/redoc\n")


if __name__ == "__main__":
    print("=" * 70)
    print("Medical Bill Extraction API - Test Suite (HackRx Datathon)")
    print("=" * 70)
    print()
    
    test_health()
    
    test_api_docs()
    
    sample_url = "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png"
    test_extract_bill_data(sample_url)
    
    print("=" * 70)
    print("Test suite complete!")
    print("=" * 70)
