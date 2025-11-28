"""
Visualize preprocessing improvements on a sample image.
"""

import sys
import os
from PIL import Image
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from advanced_preprocessing import (
    enhance_for_ocr,
    adaptive_binarization,
    create_multiple_variants,
    get_best_preprocessing_pipeline
)

def show_preprocessing_comparison(image_path: str):
    """Show before/after preprocessing comparison."""
    
    if not os.path.exists(image_path):
        print(f"Error: Image not found: {image_path}")
        return
    
    print(f"Processing: {os.path.basename(image_path)}")
    
    # Load original
    original = Image.open(image_path).convert('RGB')
    orig_array = np.array(original)
    
    print(f"Original size: {orig_array.shape[1]}x{orig_array.shape[0]}px")
    
    # Apply best preprocessing
    enhanced = get_best_preprocessing_pipeline(orig_array)
    
    print(f"Enhanced size: {enhanced.shape[1]}x{enhanced.shape[0]}px")
    
    # Save comparison
    output_dir = "preprocessing_output"
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    
    # Save original
    orig_path = os.path.join(output_dir, f"{base_name}_original.png")
    Image.fromarray(orig_array).save(orig_path)
    print(f"Saved original: {orig_path}")
    
    # Save enhanced
    enhanced_path = os.path.join(output_dir, f"{base_name}_enhanced.png")
    Image.fromarray(enhanced).save(enhanced_path)
    print(f"Saved enhanced: {enhanced_path}")
    
    # Create variants
    variants = create_multiple_variants(orig_array)
    for variant_name, variant_img in variants:
        variant_path = os.path.join(output_dir, f"{base_name}_{variant_name}.png")
        Image.fromarray(variant_img).save(variant_path)
        print(f"Saved variant: {variant_path}")
    
    print(f"\n✓ All preprocessed images saved to: {output_dir}/")
    print(f"  Compare original vs enhanced to see improvements")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Try to find a sample in TRAINING_SAMPLES
        if os.path.exists("TRAINING_SAMPLES"):
            from pdf2image import convert_from_path
            import glob
            
            pdfs = glob.glob("TRAINING_SAMPLES/*.pdf")
            if pdfs:
                print(f"Converting first page of {os.path.basename(pdfs[0])} to test...")
                images = convert_from_path(pdfs[0], first_page=1, last_page=1, dpi=300)
                temp_img = "temp_test_page.png"
                images[0].save(temp_img)
                image_path = temp_img
            else:
                print("Usage: python show_preprocessing.py <image_path>")
                print("No training samples found to test with")
                exit(1)
        else:
            print("Usage: python show_preprocessing.py <image_path>")
            exit(1)
    
    show_preprocessing_comparison(image_path)
