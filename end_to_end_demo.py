from image_pipeline import process_document
from extraction_prompts import create_extraction_prompt, validate_extraction_response
from reconciliation import reconcile_extractions, format_final_output, validate_reconciliation_output
import json


def simulate_llm_extraction(prompt_data: dict, page_no: str) -> dict:
    """
    Simulate LLM extraction response.
    In production, this would call your Gemini API with the prompts and images.
    """
    mock_responses = {
        "1": {
            "page_no": "1",
            "page_type": "Pharmacy",
            "bill_items": [
                {
                    "item_name": "Paracetamol 500mg",
                    "item_amount": 45.00,
                    "item_rate": 15.00,
                    "item_quantity": 3.00
                },
                {
                    "item_name": "Amoxicillin 250mg",
                    "item_amount": 120.50,
                    "item_rate": 40.17,
                    "item_quantity": 3.00
                },
                {
                    "item_name": "Vitamin D3 Capsules",
                    "item_amount": 280.00,
                    "item_rate": 28.00,
                    "item_quantity": 10.00
                }
            ]
        },
        "2": {
            "page_no": "2",
            "page_type": "Bill Detail",
            "bill_items": [
                {
                    "item_name": "Consultation Fee",
                    "item_amount": 500.00,
                    "item_rate": None,
                    "item_quantity": 1.00
                },
                {
                    "item_name": "Lab Test - CBC",
                    "item_amount": 350.00,
                    "item_rate": 350.00,
                    "item_quantity": 1.00
                },
                {
                    "item_name": "Paracetamol 500mg",
                    "item_amount": 45.00,
                    "item_rate": 15.00,
                    "item_quantity": 3.00
                }
            ]
        }
    }
    
    return mock_responses.get(page_no, {
        "page_no": page_no,
        "page_type": "Other",
        "bill_items": []
    })


def end_to_end_pipeline(document_url: str, output_dir: str = "./processed") -> dict:
    """
    Complete end-to-end pipeline from document to final JSON output.
    
    Args:
        document_url: URL or path to document
        output_dir: Directory for processed images
    
    Returns:
        Final datathon output dictionary
    """
    print("Step 1: Processing document and generating crops...")
    pages_metadata = process_document(document_url, output_dir)
    print(f"  Processed {len(pages_metadata)} page(s)")
    
    print("\nStep 2: Extracting bill items from each page...")
    extracted_pages = []
    
    for page_meta in pages_metadata:
        page_no = str(page_meta['page_no'])
        full_image_path = page_meta['full_image_path']
        
        region_images = []
        for crop in page_meta['crops'][1:6]:
            region_images.append({
                "crop_id": crop['crop_id'],
                "bbox": crop['bbox'],
                "image": crop['path']
            })
        
        prompt_data = create_extraction_prompt(
            page_no=page_no,
            page_type_hint="Bill Detail | Final Bill | Pharmacy | Other",
            full_page_image_ref=full_image_path,
            region_images=region_images
        )
        
        print(f"  Page {page_no}: Created extraction prompt")
        
        llm_response = simulate_llm_extraction(prompt_data, page_no)
        
        is_valid = validate_extraction_response(llm_response)
        print(f"  Page {page_no}: Extracted {len(llm_response.get('bill_items', []))} items (valid: {is_valid})")
        
        if is_valid:
            extracted_pages.append(llm_response)
    
    print("\nStep 3: Reconciling extractions and computing totals...")
    reconciliation_input = {
        "pages": extracted_pages,
        "printed_totals_images": [
            {
                "page_no": "2",
                "extracted_value": 1340.50,
                "bbox": [100, 200, 300, 250]
            }
        ]
    }
    
    final_output = reconcile_extractions(reconciliation_input)
    
    is_valid_output = validate_reconciliation_output(final_output)
    print(f"  Reconciliation complete (valid: {is_valid_output})")
    print(f"  Total unique items: {final_output['data']['total_item_count']}")
    
    return final_output


def main():
    """
    Example usage of the complete pipeline.
    """
    print("=" * 70)
    print("Medical Bill Extraction Pipeline - End-to-End Demo")
    print("=" * 70)
    
    document_path = "./sample_bill.pdf"
    
    try:
        final_output = end_to_end_pipeline(document_path)
        
        print("\n" + "=" * 70)
        print("FINAL OUTPUT (Datathon Format)")
        print("=" * 70)
        print(format_final_output(final_output))
        
        print("\n" + "=" * 70)
        print("Page-wise Summary:")
        print("=" * 70)
        for page in final_output['data']['pagewise_line_items']:
            print(f"\nPage {page['page_no']} ({page['page_type']}):")
            for item in page['bill_items']:
                amount = f"₹{item['item_amount']:.2f}" if item['item_amount'] is not None else "N/A"
                print(f"  - {item['item_name']}: {amount}")
        
        total_amount = sum(
            item['item_amount'] 
            for page in final_output['data']['pagewise_line_items'] 
            for item in page['bill_items'] 
            if item['item_amount'] is not None
        )
        print(f"\nTotal Bill Amount: ₹{total_amount:.2f}")
        print(f"Total Unique Items: {final_output['data']['total_item_count']}")
        
    except Exception as e:
        print(f"\nError in pipeline: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
