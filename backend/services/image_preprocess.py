"""
Image Preprocessing Service for OCR

Uses OpenCV to enhance difficult images (low contrast, shadows, wrinkled paper)
before sending them to the OCR Engine.
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def preprocess_image_for_ocr(file_bytes: bytes) -> bytes:
    """
    Enhance image quality for OCR:
      1. Resize (2x) to make text larger
      2. Grayscale conversion
      3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
      4. Median Blur to remove pepper noise
    
    Returns:
        Processed image as PNG bytes.
    """
    try:
        # Convert raw bytes to numpy array for OpenCV
        np_arr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.warning("OpenCV could not decode the image. Returning original bytes.")
            return file_bytes

        # 1. Resize (improves OCR)
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # 2. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Increase Contrast (CLAHE is vastly superior to Thresholding for EasyOCR)
        # EasyOCR is a deep-learning model trained on natural gradients. 
        # Binarizing the image (Thresholding) destroys its accuracy.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(gray)

        # 4. Noise removal
        processed = cv2.medianBlur(contrast_enhanced, 3)

        # ── DEBUG: Save the processed image to disk so we can see it! ──
        cv2.imwrite("debug_processed.png", processed)

        # Encode back to PNG bytes
        success, encoded_img = cv2.imencode('.png', processed)
        if not success:
            logger.warning("OpenCV failed to encode processed image. Returning original bytes.")
            return file_bytes
            
        logger.info("Image preprocessing completed successfully.")
        return encoded_img.tobytes()

    except Exception as e:
        logger.error("Image preprocessing failed: %s", e)
        # Fallback to original bytes so OCR can at least try
        return file_bytes
