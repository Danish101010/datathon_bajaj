"""
Test script to evaluate extraction performance on training samples.
"""

import os
import json
import time
from pathlib import Path
import requests

API_URL = "http://localhost:8000/extract-bill-data"
TRAINING_DIR = "TRAINING_SAMPLES"

def test_single_file(file_path: str) -> dict:
    """Test extraction on a single PDF file."""
    print(f"\n{'='*80}")
    print(f"Testing: {os.path.basename(file_path)}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    with open(file_path, 'rb') as f:
        files = {'document': (os.path.basename(file_path), f, 'application/pdf')}
        
        try:
            response = requests.post(API_URL, files=files, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            elapsed = time.time() - start_time
            
            # Print summary
            total_items = len(result.get('bill_items', []))
            total_amount = result.get('reconciled_amount', 0)
            
            print(f"\n✓ SUCCESS")
            print(f"  Items extracted: {total_items}")
            print(f"  Total amount: ₹{total_amount:,.2f}")
            print(f"  Time taken: {elapsed:.2f}s")
            
            # Print first 5 items
            if total_items > 0:
                print(f"\n  Sample items (first 5):")
                for item in result['bill_items'][:5]:
                    print(f"    - {item['item_name']}: ₹{item['item_amount']:.2f}")
                if total_items > 5:
                    print(f"    ... and {total_items - 5} more items")
            
            return {
                'file': os.path.basename(file_path),
                'status': 'success',
                'items_count': total_items,
                'total_amount': total_amount,
                'time_seconds': elapsed,
                'result': result
            }
            
        except requests.exceptions.Timeout:
            print(f"\n✗ TIMEOUT after 120s")
            return {
                'file': os.path.basename(file_path),
                'status': 'timeout',
                'error': 'Request timeout'
            }
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            return {
                'file': os.path.basename(file_path),
                'status': 'error',
                'error': str(e)
            }

def test_all_samples():
    """Test all training samples."""
    if not os.path.exists(TRAINING_DIR):
        print(f"Error: {TRAINING_DIR} directory not found")
        return
    
    pdf_files = sorted(Path(TRAINING_DIR).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {TRAINING_DIR}")
        return
    
    print(f"Found {len(pdf_files)} training samples")
    print(f"Testing with improved preprocessing + gemini-1.5-flash\n")
    
    results = []
    total_start = time.time()
    curr = 1
    for pdf_file in pdf_files:
        if curr >= 4:
            break
        result = test_single_file(str(pdf_file))
        results.append(result)
        curr += 1
        time.sleep(1)  # Brief pause between requests
    
    total_elapsed = time.time() - total_start
    
    # Summary statistics
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']
    
    print(f"\nTotal files tested: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Total time: {total_elapsed/60:.2f} minutes")
    
    if successful:
        avg_items = sum(r['items_count'] for r in successful) / len(successful)
        avg_time = sum(r['time_seconds'] for r in successful) / len(successful)
        total_amount_sum = sum(r['total_amount'] for r in successful)
        
        print(f"\nAverage items per bill: {avg_items:.1f}")
        print(f"Average processing time: {avg_time:.2f}s")
        print(f"Total extracted amount (all bills): ₹{total_amount_sum:,.2f}")
    
    # List files with 0 items
    zero_items = [r for r in successful if r['items_count'] == 0]
    if zero_items:
        print(f"\n⚠️  Files with 0 items extracted:")
        for r in zero_items:
            print(f"  - {r['file']}")
    
    # List failed files
    if failed:
        print(f"\n✗ Failed files:")
        for r in failed:
            print(f"  - {r['file']}: {r.get('error', 'Unknown error')}")
    
    # Save detailed results
    output_file = "test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print("✓ API server is running\n")
    except:
        print("✗ ERROR: API server is not running!")
        print("Please start the server first: python api.py")
        exit(1)
    
    test_all_samples()
