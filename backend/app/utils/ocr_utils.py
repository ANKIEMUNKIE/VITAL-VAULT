# app/utils/ocr_utils.py
"""Image preprocessing utilities for OCR optimization.

Applies deskewing, denoising, and binarization to improve
Tesseract OCR accuracy on medical documents.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def preprocess_image(image_path: str) -> str:
    """Preprocess an image for optimal OCR extraction.

    Steps:
    1. Load image with OpenCV.
    2. Convert to grayscale.
    3. Apply Gaussian blur for denoising.
    4. Apply adaptive thresholding for binarization.
    5. Save processed image.

    Args:
        image_path: Path to the source image file.

    Returns:
        Path to the preprocessed image.
    """
    try:
        import cv2
        import numpy as np

        img = cv2.imread(image_path)
        if img is None:
            logger.warning("Could not load image: %s", image_path)
            return image_path

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.GaussianBlur(gray, (5, 5), 0)

        # Binarize using adaptive thresholding
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2,
        )

        # Save processed image
        processed_path = f"{os.path.splitext(image_path)[0]}_processed.png"
        cv2.imwrite(processed_path, binary)

        logger.info("Image preprocessed: %s → %s", image_path, processed_path)
        return processed_path

    except ImportError:
        logger.warning("OpenCV not available — skipping preprocessing")
        return image_path

    except Exception:
        logger.exception("Image preprocessing failed for %s", image_path)
        return image_path
