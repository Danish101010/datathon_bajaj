"""
Advanced image preprocessing optimized for medical bill extraction.
Includes OCR-focused enhancements, text area detection, and adaptive binarization.
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import List, Tuple
import os


def enhance_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Apply aggressive OCR-focused enhancements.
    
    Args:
        image: Input image as numpy array (RGB)
    
    Returns:
        Enhanced image optimized for text extraction
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Denoise while preserving edges
    denoised = cv2.fastNlMeansDenoising(enhanced, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # Sharpen to enhance text edges
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    
    # Convert back to RGB
    result = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)
    
    return result


def adaptive_binarization(image: np.ndarray) -> np.ndarray:
    """
    Apply adaptive thresholding to create high-contrast binary image.
    
    Args:
        image: Input image as numpy array (RGB)
    
    Returns:
        Binarized image
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Adaptive thresholding
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2
    )
    
    # Convert back to RGB
    result = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
    
    return result


def detect_text_regions(image: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Detect regions containing text using MSER or contour detection.
    
    Args:
        image: Input image as numpy array (RGB)
    
    Returns:
        List of bounding boxes (x, y, w, h) for text regions
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Apply morphological operations to connect text regions
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 3))
    dilated = cv2.dilate(gray, kernel, iterations=2)
    
    # Find contours
    contours, _ = cv2.findContours(255 - dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter and sort text regions
    text_regions = []
    h, w = image.shape[:2]
    
    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        
        # Filter out tiny or huge regions
        if cw < w * 0.05 or ch < h * 0.01:
            continue
        if cw > w * 0.95 or ch > h * 0.9:
            continue
        
        text_regions.append((x, y, cw, ch))
    
    return sorted(text_regions, key=lambda r: (r[1], r[0]))  # Sort top-to-bottom, left-to-right


def remove_borders_and_lines(image: np.ndarray) -> np.ndarray:
    """
    Remove table borders and horizontal/vertical lines that might confuse OCR.
    
    Args:
        image: Input image as numpy array (RGB)
    
    Returns:
        Image with borders/lines removed
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    detect_horizontal = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    
    # Detect vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    detect_vertical = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    
    # Combine line masks
    lines_mask = cv2.add(detect_horizontal, detect_vertical)
    
    # Remove lines from original image
    result = gray.copy()
    result[lines_mask > 0] = 255
    
    # Convert back to RGB
    result = cv2.cvtColor(result, cv2.COLOR_GRAY2RGB)
    
    return result


def resize_for_optimal_ocr(image: np.ndarray, target_height: int = 2000) -> np.ndarray:
    """
    Resize image to optimal resolution for OCR (not too small, not too large).
    
    Args:
        image: Input image as numpy array (RGB)
        target_height: Target height in pixels
    
    Returns:
        Resized image
    """
    h, w = image.shape[:2]
    
    if h < target_height * 0.8:
        # Upscale small images
        scale = target_height / h
        new_width = int(w * scale)
        resized = cv2.resize(image, (new_width, target_height), interpolation=cv2.INTER_CUBIC)
    elif h > target_height * 1.5:
        # Downscale large images
        scale = target_height / h
        new_width = int(w * scale)
        resized = cv2.resize(image, (new_width, target_height), interpolation=cv2.INTER_AREA)
    else:
        resized = image
    
    return resized




def preprocess_bill_image(image_path: str, output_dir: str = None) -> str:
    """
    Main preprocessing function that generates a single optimized image of a bill.
    
    Args:
        image_path: Path to input image
        output_dir: Directory to save the preprocessed image (optional)
    
    Returns:
        Path to preprocessed image
    """
    pil_img = Image.open(image_path).convert('RGB')
    img_array = np.array(pil_img)
    img_array = get_best_preprocessing_pipeline(img_array)
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_preprocessed.png")
        pil_variant = Image.fromarray(img_array)
        pil_variant.save(output_path)
        return output_path
    else:
        # If no output_dir, just return the processed image path (not saved)
        return None


def get_best_preprocessing_pipeline(image: np.ndarray) -> np.ndarray:
    """
    Apply the single best preprocessing pipeline for medical bills.
    This is optimized based on testing with medical bill samples.
    
    Args:
        image: Input image as numpy array (RGB)
    
    Returns:
        Preprocessed image ready for LLM extraction
    """
    # Resize to optimal resolution (2000-2500px height)
    image = resize_for_optimal_ocr(image, target_height=2200)
    
    # Apply OCR-focused enhancement
    enhanced = enhance_for_ocr(image)
    
    # Additional sharpening
    pil_img = Image.fromarray(enhanced)
    sharpened = pil_img.filter(ImageFilter.SHARPEN)
    
    # Increase contrast
    contrast_enhanced = ImageEnhance.Contrast(sharpened).enhance(1.8)
    
    # Increase brightness slightly
    brightness_enhanced = ImageEnhance.Brightness(contrast_enhanced).enhance(1.1)
    
    return np.array(brightness_enhanced)
