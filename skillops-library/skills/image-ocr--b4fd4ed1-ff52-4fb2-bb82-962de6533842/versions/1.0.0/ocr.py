#!/usr/bin/env python3
"""Image OCR - Extract text from images using Tesseract.

Usage: python3 ocr.py <image_path> [--lang chi_sim+eng] [--preprocess]
"""
import sys
import subprocess
import argparse
from pathlib import Path

def ocr_image(image_path: str, lang: str = "chi_sim+eng", preprocess: bool = True) -> str:
    """Run OCR on an image and return extracted text."""
    path = Path(image_path)
    if not path.exists():
        return f"ERROR: File not found: {image_path}"

    # Optional preprocessing with Pillow for better OCR accuracy
    if preprocess:
        try:
            from PIL import Image, ImageFilter, ImageEnhance
            img = Image.open(path)
            # Convert to grayscale
            img = img.convert('L')
            # Increase contrast
            img = ImageEnhance.Contrast(img).enhance(2.0)
            # Sharpen
            img = img.filter(ImageFilter.SHARPEN)
            # Save to temp
            preprocessed = path.parent / f"_ocr_preprocessed_{path.name}"
            img.save(preprocessed)
            path = preprocessed
        except Exception as e:
            pass  # Fall back to original image

    # Run tesseract
    try:
        result = subprocess.run(
            ['tesseract', str(path), 'stdout', '-l', lang, '--psm', '6'],
            capture_output=True, text=True, timeout=30
        )
        text = result.stdout.strip()
        if not text and result.stderr:
            # Try with psm 3 (auto) if psm 6 failed
            result = subprocess.run(
                ['tesseract', str(path), 'stdout', '-l', lang, '--psm', '3'],
                capture_output=True, text=True, timeout=30
            )
            text = result.stdout.strip()

        # Cleanup preprocessed file
        if preprocess:
            preprocessed_file = path.parent / f"_ocr_preprocessed_{path.name}"
            if preprocessed_file.exists():
                preprocessed_file.unlink()

        return text if text else "(No text detected in image)"
    except subprocess.TimeoutExpired:
        return "ERROR: OCR timed out"
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR image text extraction")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--lang", default="chi_sim+eng", help="Tesseract language (default: chi_sim+eng)")
    parser.add_argument("--no-preprocess", action="store_true", help="Skip image preprocessing")
    args = parser.parse_args()

    result = ocr_image(args.image, lang=args.lang, preprocess=not args.no_preprocess)
    print(result)
