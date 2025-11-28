import io
import os
import tempfile
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import requests
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
from pdf2image import convert_from_bytes
import cv2


def download_document(url: str, output_dir: Optional[str] = None) -> Union[str, bytes]:
    """
    Download a document from URL. Supports JPG, PNG, PDF formats.
    
    Args:
        url: URL of the document to download
        output_dir: Optional directory to save the file. If None, returns bytes.
    
    Returns:
        File path if output_dir specified, otherwise bytes
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    content_type = response.headers.get('content-type', '').lower()
    extension = None
    
    if 'pdf' in content_type or url.lower().endswith('.pdf'):
        extension = '.pdf'
    elif 'jpeg' in content_type or 'jpg' in content_type or url.lower().endswith(('.jpg', '.jpeg')):
        extension = '.jpg'
    elif 'png' in content_type or url.lower().endswith('.png'):
        extension = '.png'
    else:
        extension = '.pdf'
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"document{extension}")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    
    return response.content


def pdf_to_images(pdf_path_or_bytes: Union[str, bytes], output_dir: Optional[str] = None, dpi: int = 300) -> List[str]:
    """
    Convert PDF pages to high-resolution PNG images.
    
    Args:
        pdf_path_or_bytes: Path to PDF file or PDF bytes
        output_dir: Directory to save images. If None, uses temp directory.
        dpi: Resolution for rendering (default 300 DPI)
    
    Returns:
        List of paths to rendered PNG images
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    if isinstance(pdf_path_or_bytes, bytes):
        images = convert_from_bytes(pdf_path_or_bytes, dpi=dpi)
    else:
        with open(pdf_path_or_bytes, 'rb') as f:
            pdf_bytes = f.read()
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
    
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(output_dir, f"page_{i+1}.png")
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
    
    return image_paths


def _deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Deskew an image using OpenCV.
    
    Args:
        image: Input image as numpy array
    
    Returns:
        Deskewed image
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return image
    
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    if abs(angle) < 0.5:
        return image
    
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated


def _denoise_image(image: np.ndarray) -> np.ndarray:
    """
    Denoise image using Non-local Means Denoising.
    
    Args:
        image: Input image as numpy array
    
    Returns:
        Denoised image
    """
    return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)


def _increase_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """
    Increase image contrast.
    
    Args:
        image: PIL Image
        factor: Contrast enhancement factor
    
    Returns:
        Enhanced PIL Image
    """
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def _auto_crop_margins(image: np.ndarray, threshold: int = 240) -> np.ndarray:
    """
    Auto-crop white margins from image.
    
    Args:
        image: Input image as numpy array
        threshold: Pixel value threshold for white detection
    
    Returns:
        Cropped image
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
    mask = gray < threshold
    
    coords = np.argwhere(mask)
    if len(coords) == 0:
        return image
    
    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)
    
    margin = 10
    y_min = max(0, y_min - margin)
    x_min = max(0, x_min - margin)
    y_max = min(image.shape[0], y_max + margin)
    x_max = min(image.shape[1], x_max + margin)
    
    return image[y_min:y_max, x_min:x_max]


def _generate_column_crops(image: np.ndarray, num_columns: int) -> List[Tuple[int, np.ndarray, List[int]]]:
    """
    Generate column-based crops.
    
    Args:
        image: Input image as numpy array
        num_columns: Number of columns to create (2-4)
    
    Returns:
        List of tuples (crop_id, crop_image, bbox)
    """
    h, w = image.shape[:2]
    crops = []
    
    if num_columns == 2:
        mid = w // 2
        crops.append((1, image[:, :mid], [0, 0, mid, h]))
        crops.append((2, image[:, mid:], [mid, 0, w, h]))
    elif num_columns == 3:
        third = w // 3
        crops.append((1, image[:, :third], [0, 0, third, h]))
        crops.append((2, image[:, third:2*third], [third, 0, 2*third, h]))
        crops.append((3, image[:, 2*third:], [2*third, 0, w, h]))
    elif num_columns == 4:
        quarter = w // 4
        for i in range(4):
            start = i * quarter
            end = w if i == 3 else (i + 1) * quarter
            crops.append((i+1, image[:, start:end], [start, 0, end, h]))
    
    return crops


def _generate_sliding_window_crops(
    image: np.ndarray,
    window_width: int = 3000,
    window_height: int = 800,
    overlap_ratio: float = 0.2
) -> List[Tuple[int, np.ndarray, List[int]]]:
    """
    Generate sliding window crops for table extraction.
    
    Args:
        image: Input image as numpy array
        window_width: Width of sliding window
        window_height: Height of sliding window
        overlap_ratio: Overlap between consecutive windows
    
    Returns:
        List of tuples (crop_id, crop_image, bbox)
    """
    h, w = image.shape[:2]
    crops = []
    crop_id = 1
    
    scale_w = min(1.0, w / window_width)
    scale_h = min(1.0, h / window_height)
    scale = min(scale_w, scale_h)
    
    actual_window_width = int(window_width * scale)
    actual_window_height = int(window_height * scale)
    
    step_y = int(actual_window_height * (1 - overlap_ratio))
    step_x = int(actual_window_width * (1 - overlap_ratio))
    
    y = 0
    while y < h:
        x = 0
        while x < w:
            y_end = min(y + actual_window_height, h)
            x_end = min(x + actual_window_width, w)
            
            crop = image[y:y_end, x:x_end]
            crops.append((crop_id, crop, [x, y, x_end, y_end]))
            crop_id += 1
            
            x += step_x
            if x >= w:
                break
        
        y += step_y
        if y >= h:
            break
    
    return crops


def preprocess_image(
    image_path: str,
    page_no: int = 1,
    output_dir: Optional[str] = None
) -> Dict:
    """
    Preprocess image with deskew, denoise, contrast enhancement, auto-crop, and generate crops.
    
    Args:
        image_path: Path to input image
        page_no: Page number for metadata
        output_dir: Directory to save processed images. If None, uses temp directory.
    
    Returns:
        Dictionary with metadata:
        {
            'page_no': int,
            'full_image_path': str,
            'crops': [
                {'crop_id': str, 'path': str, 'bbox': [x1, y1, x2, y2]},
                ...
            ]
        }
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    image = Image.open(image_path)
    image = image.convert('RGB')
    
    img_array = np.array(image)
    
    img_array = _deskew_image(img_array)
    img_array = _denoise_image(img_array)
    
    pil_image = Image.fromarray(img_array)
    pil_image = _increase_contrast(pil_image, factor=1.5)
    
    img_array = np.array(pil_image)
    img_array = _auto_crop_margins(img_array)
    
    full_image_path = os.path.join(output_dir, f"page_{page_no}_processed.png")
    Image.fromarray(img_array).save(full_image_path)
    
    crops_metadata = []
    
    full_crop = {
        'crop_id': f'p{page_no}_full',
        'path': full_image_path,
        'bbox': [0, 0, img_array.shape[1], img_array.shape[0]]
    }
    crops_metadata.append(full_crop)
    
    for num_cols in [2, 3, 4]:
        column_crops = _generate_column_crops(img_array, num_cols)
        for crop_id, crop_img, bbox in column_crops:
            crop_path = os.path.join(output_dir, f"page_{page_no}_col{num_cols}_{crop_id}.png")
            Image.fromarray(crop_img).save(crop_path)
            crops_metadata.append({
                'crop_id': f'p{page_no}_col{num_cols}_{crop_id}',
                'path': crop_path,
                'bbox': bbox
            })
    
    sliding_crops = _generate_sliding_window_crops(img_array)
    for crop_id, crop_img, bbox in sliding_crops:
        crop_path = os.path.join(output_dir, f"page_{page_no}_slide_{crop_id}.png")
        Image.fromarray(crop_img).save(crop_path)
        crops_metadata.append({
            'crop_id': f'p{page_no}_slide_{crop_id}',
            'path': crop_path,
            'bbox': bbox
        })
    
    return {
        'page_no': page_no,
        'full_image_path': full_image_path,
        'crops': crops_metadata
    }


def process_document(
    document_source: Union[str, bytes],
    output_dir: Optional[str] = None
) -> List[Dict]:
    """
    Process a complete document (PDF or image) and return preprocessing metadata for all pages.
    
    Args:
        document_source: URL, file path, or bytes of document
        output_dir: Directory to save processed images. If None, uses temp directory.
    
    Returns:
        List of page metadata dictionaries
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    if isinstance(document_source, str) and document_source.startswith(('http://', 'https://')):
        doc_content = download_document(document_source)
    else:
        doc_content = document_source
    
    if isinstance(doc_content, str):
        file_path = doc_content
    else:
        temp_file = os.path.join(output_dir, 'temp_document')
        with open(temp_file, 'wb') as f:
            f.write(doc_content)
        file_path = temp_file
    
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf' or (isinstance(doc_content, bytes) and doc_content[:4] == b'%PDF'):
        image_paths = pdf_to_images(file_path, output_dir)
    else:
        image_paths = [file_path]
    
    results = []
    for page_no, img_path in enumerate(image_paths, start=1):
        page_metadata = preprocess_image(img_path, page_no, output_dir)
        results.append(page_metadata)
    
    return results
