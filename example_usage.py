from image_pipeline import process_document, preprocess_image, download_document, pdf_to_images
from extraction_prompts import create_extraction_prompt, validate_extraction_response
import json


def main():
    url = "https://example.com/medical_bill.pdf"
    
    output_dir = "./processed_images"
    
    pages_metadata = process_document(url, output_dir)
    
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
        
        print(f"\n=== Page {page_no} ===")
        print(f"System Prompt: {prompt_data['system_prompt'][:100]}...")
        print(f"User Prompt Length: {len(prompt_data['user_prompt'])} chars")
        
        llm_response = {
            "page_no": page_no,
            "page_type": "Pharmacy",
            "bill_items": [
                {
                    "item_name": "Livi 300mg Tab",
                    "item_quantity": 14.00,
                    "item_rate": 32.00,
                    "item_amount": 448.00
                },
                {
                    "item_name": "Amoxicillin 500mg",
                    "item_quantity": 3.00,
                    "item_rate": None,
                    "item_amount": 150.00
                }
            ]
        }
        
        is_valid = validate_extraction_response(llm_response)
        print(f"Response Valid: {is_valid}")
        print(f"Extracted Items: {len(llm_response['bill_items'])}")
        print(json.dumps(llm_response, indent=2))


if __name__ == "__main__":
    main()
