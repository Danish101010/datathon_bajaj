from typing import Dict, List, Optional, Tuple
import json


def deduplicate_items(all_items: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Deduplicate exact duplicate items across pages based on item_name and item_amount.
    
    Args:
        all_items: List of all bill items from all pages
    
    Returns:
        Tuple of (deduplicated items list, count of unique items)
    """
    seen = set()
    deduplicated = []
    
    for item in all_items:
        item_name = item.get('item_name', '').strip()
        item_amount = item.get('item_amount')
        
        key = (item_name, item_amount)
        
        if key not in seen:
            seen.add(key)
            deduplicated.append(item)
    
    return deduplicated, len(deduplicated)


def compute_reconciled_amount(items: List[Dict]) -> float:
    """
    Compute sum of all numeric item_amounts (skip nulls).
    
    Args:
        items: List of bill items
    
    Returns:
        Total reconciled amount as float with 2 decimal places
    """
    total = 0.0
    
    for item in items:
        amount = item.get('item_amount')
        if amount is not None and isinstance(amount, (int, float)):
            total += float(amount)
    
    return round(total, 2)


def verify_printed_totals(reconciled_amount: float, printed_totals_images: List[Dict]) -> Dict:
    """
    Internal diagnostics: compare reconciled amount to printed totals.
    Note: Visual verification would be done by LLM. This provides structure for delta calculation.
    
    Args:
        reconciled_amount: Computed reconciled amount
        printed_totals_images: List of printed total image references with extracted values
    
    Returns:
        Diagnostics dict (not included in final output)
    """
    diagnostics = {
        "reconciled_amount": reconciled_amount,
        "printed_totals": [],
        "deltas": []
    }
    
    for printed_total in printed_totals_images:
        page_no = printed_total.get('page_no')
        extracted_total = printed_total.get('extracted_value')
        
        if extracted_total is not None:
            delta = round(float(extracted_total) - reconciled_amount, 2)
            diagnostics['printed_totals'].append({
                'page_no': page_no,
                'printed_total': extracted_total,
                'delta': delta
            })
            diagnostics['deltas'].append(delta)
    
    return diagnostics


def reconcile_extractions(input_data: Dict) -> Dict:
    """
    Reconcile pagewise extractions into final datathon output format.
    
    Args:
        input_data: Dictionary containing:
            - pages: List of page extractions with bill_items
            - printed_totals_images: Optional list of printed total references
    
    Returns:
        Final JSON output matching datathon schema
    """
    pages = input_data.get('pages', [])
    printed_totals_images = input_data.get('printed_totals_images', [])
    
    pagewise_line_items = []
    all_items = []
    is_success = True
    
    for page in pages:
        page_no = page.get('page_no')
        page_type = page.get('page_type', 'Other')
        bill_items = page.get('bill_items', [])
        
        page_entry = {
            'page_no': page_no,
            'page_type': page_type,
            'bill_items': []
        }
        
        for item in bill_items:
            formatted_item = {
                'item_name': item.get('item_name', ''),
                'item_amount': round(item['item_amount'], 2) if item.get('item_amount') is not None else None,
                'item_rate': round(item['item_rate'], 2) if item.get('item_rate') is not None else None,
                'item_quantity': round(item['item_quantity'], 2) if item.get('item_quantity') is not None else None
            }
            page_entry['bill_items'].append(formatted_item)
            all_items.append(formatted_item)
        
        pagewise_line_items.append(page_entry)
    
    deduplicated_items, total_item_count = deduplicate_items(all_items)
    
    reconciled_amount = compute_reconciled_amount(all_items)
    
    if printed_totals_images:
        diagnostics = verify_printed_totals(reconciled_amount, printed_totals_images)
    
    if len(pages) == 0:
        is_success = False
    
    output = {
        'is_success': is_success,
        'token_usage': {
            'total_tokens': 0,
            'input_tokens': 0,
            'output_tokens': 0
        },
        'data': {
            'pagewise_line_items': pagewise_line_items,
            'total_item_count': total_item_count
        }
    }
    
    return output


def format_final_output(output: Dict) -> str:
    """
    Format final output as exact JSON string.
    
    Args:
        output: Output dictionary
    
    Returns:
        JSON string
    """
    return json.dumps(output, indent=2, ensure_ascii=False)


def validate_reconciliation_output(output: Dict) -> bool:
    """
    Validate that reconciliation output follows the required schema.
    
    Args:
        output: Output dictionary
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(output, dict):
        return False
    
    required_keys = ['is_success', 'token_usage', 'data']
    if not all(key in output for key in required_keys):
        return False
    
    if not isinstance(output['is_success'], bool):
        return False
    
    token_usage = output.get('token_usage', {})
    required_token_keys = ['total_tokens', 'input_tokens', 'output_tokens']
    if not all(key in token_usage for key in required_token_keys):
        return False
    
    data = output.get('data', {})
    if 'pagewise_line_items' not in data or 'total_item_count' not in data:
        return False
    
    if not isinstance(data['pagewise_line_items'], list):
        return False
    
    if not isinstance(data['total_item_count'], int):
        return False
    
    for page in data['pagewise_line_items']:
        if not isinstance(page, dict):
            return False
        if 'page_no' not in page or 'page_type' not in page or 'bill_items' not in page:
            return False
        if not isinstance(page['bill_items'], list):
            return False
    
    return True
