EXTRACTION_SYSTEM_PROMPT = """You are a deterministic, safety-minded extractor. You will be given one page image (and optionally several region crop images) from a medical/pharmacy bill. DO NOT produce any commentary — output EXACT JSON only following the datathon schema. Use numeric floats (two decimal places) for amounts, rates, quantities. If a numeric value cannot be found, set it to null. Do not hallucinate items. When making choices, prefer visual evidence (text present in the image). Always use temperature = 0.

CRITICAL: If you see ANY bill items in the image, you MUST extract them. An empty bill_items array should ONLY be returned if the image truly contains no line items at all. Double-check the images before returning empty results."""

EXTRACTION_USER_PROMPT_TEMPLATE = """Input:
{input_json}

Task:
From the supplied images extract a JSON object for **this page** containing the list of bill line items visible on the page.

IMPORTANT: Examine ALL images carefully. Look for ANY items, services, medicines, tests, charges, or line items with names and amounts. Even if the layout is unconventional, extract ALL visible line items.

Rules (strict):
1. Inspect the **images** visually. Use the full page first; confirm ambiguous numbers by checking the relevant crop images.
2. Extract EVERY line item you see - medicines, services, tests, procedures, consultations, room charges, etc.
3. Each bill item must have:
   - "item_name": text exactly as printed on the bill (trim whitespace). Include full item description.
   - "item_amount": Net Amount after discount as printed (float or null).
   - "item_rate": Rate as printed (float or null).
   - "item_quantity": Quantity as printed (float or null).
4. If the printed layout is tabular, prefer the right-most numeric column as item_amount.
5. Normalize numeric formats: remove currency symbols and thousands separators. Output floats with two decimals (e.g., 1234.50).
6. If the item name wraps across lines, combine visually adjacent lines that belong to the same row.
7. If a numeric value is illegible or missing, set it to null (do not guess). Only infer rate or quantity if Rate * Quantity equals Amount within 1% AND all three numbers are clearly readable.
8. If multiple distinct numeric candidates are present near the item text, choose the numeric that aligns visually in the same row (same baseline) or the rightmost numeric.
9. For page_type, choose the most appropriate: "Bill Detail" (has itemized list), "Final Bill" (summary with totals), "Pharmacy" (medicine list), or "Other" (only if truly unclear).
10. Output EXACT JSON and nothing else.

REMINDER: If you see ANY items in the images, you MUST extract them. Empty bill_items should ONLY occur if there are genuinely no line items visible at all.

Return JSON:
{{
  "page_no": "{page_no}",
  "page_type": "Bill Detail | Final Bill | Pharmacy | Other",
  "bill_items": [
    {{
      "item_name": "string",
      "item_amount": 123.45 or null,
      "item_rate": 12.34 or null,
      "item_quantity": 2.00 or null
    }},
    ...
  ]
}}

Examples:
1) If crop shows row: "Livi 300mg Tab     14    32.00    448.00" → {{"item_name":"Livi 300mg Tab","item_quantity":14.00,"item_rate":32.00,"item_amount":448.00}}
2) If item line shows only "Amox 500mg  3  Rs.150" and no rate, assume last numeric = amount → {{"item_name":"Amox 500mg","item_quantity":3.00,"item_rate":null,"item_amount":150.00}}
"""


def create_extraction_prompt(page_no: str, page_type_hint: str, full_page_image_ref: str, region_images: list) -> dict:
    """
    Create structured extraction prompt for LLM.
    
    Args:
        page_no: Page number
        page_type_hint: Hint about page type (e.g., "Bill Detail | Final Bill | Pharmacy | Other")
        full_page_image_ref: Reference to full page image (path or placeholder)
        region_images: List of dicts with crop_id, bbox, image reference
    
    Returns:
        Dictionary with system and user prompts
    """
    input_json = {
        "page_no": page_no,
        "page_type_hint": page_type_hint,
        "full_page_image": full_page_image_ref,
        "region_images": region_images
    }
    
    import json
    input_json_str = json.dumps(input_json, indent=2)
    
    user_prompt = EXTRACTION_USER_PROMPT_TEMPLATE.format(
        input_json=input_json_str,
        page_no=page_no
    )
    
    return {
        "system_prompt": EXTRACTION_SYSTEM_PROMPT,
        "user_prompt": user_prompt
    }


def validate_extraction_response(response: dict) -> bool:
    """
    Validate that extraction response follows the required schema.
    
    Args:
        response: Parsed JSON response from LLM
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(response, dict):
        return False
    
    required_keys = ["page_no", "page_type", "bill_items"]
    if not all(key in response for key in required_keys):
        return False
    
    if not isinstance(response["bill_items"], list):
        return False
    
    for item in response["bill_items"]:
        if not isinstance(item, dict):
            return False
        
        required_item_keys = ["item_name", "item_amount", "item_rate", "item_quantity"]
        if not all(key in item for key in required_item_keys):
            return False
        
        if not isinstance(item["item_name"], str):
            return False
        
        for numeric_field in ["item_amount", "item_rate", "item_quantity"]:
            value = item[numeric_field]
            if value is not None and not isinstance(value, (int, float)):
                return False
    
    return True


def normalize_numeric_value(value_str: str) -> float:
    """
    Normalize numeric string to float (remove currency symbols, thousands separators).
    
    Args:
        value_str: String containing numeric value
    
    Returns:
        Normalized float value with 2 decimal places
    """
    import re
    
    cleaned = re.sub(r'[₹$€£¥,\s]', '', value_str)
    
    try:
        value = float(cleaned)
        return round(value, 2)
    except ValueError:
        return None
