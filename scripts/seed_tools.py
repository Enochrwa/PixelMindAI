"""Seed the tool_catalog table with all 43 PixelMind AI tools."""

from __future__ import annotations

TOOLS = [
    # === OCR & Document Intelligence ===
    {"slug": "receipt-scanner", "name": "Receipt Scanner", "module": "ocr", "credits_cost": 1, "is_novel": False},
    {"slug": "invoice-reader", "name": "Invoice Reader", "module": "ocr", "credits_cost": 1, "is_novel": False},
    {"slug": "business-card-scanner", "name": "Business Card Scanner", "module": "ocr", "credits_cost": 1, "is_novel": False},
    {"slug": "handwriting-ocr", "name": "Handwriting OCR", "module": "ocr", "credits_cost": 2, "is_novel": False},
    {"slug": "menu-scanner", "name": "Menu Scanner & Digitizer", "module": "ocr", "credits_cost": 1, "is_novel": False},
    {"slug": "document-scanner", "name": "Document Scanner", "module": "ocr", "credits_cost": 1, "is_novel": False},
    {"slug": "signature-extractor", "name": "Signature Extractor", "module": "ocr", "credits_cost": 1, "is_novel": False},
    {"slug": "form-field-reader", "name": "Form Field Reader", "module": "ocr", "credits_cost": 2, "is_novel": True},
    # === Photo Intelligence ===
    {"slug": "background-remover", "name": "Background Remover", "module": "photo", "credits_cost": 1, "is_novel": False},
    {"slug": "passport-photo", "name": "Passport Photo Generator", "module": "photo", "credits_cost": 2, "is_novel": False},
    {"slug": "image-upscaler", "name": "Image Upscaler (4×)", "module": "photo", "credits_cost": 3, "is_novel": False},
    {"slug": "resume-photo-optimizer", "name": "Resume Photo Optimizer", "module": "photo", "credits_cost": 2, "is_novel": False},
    {"slug": "face-blur", "name": "Face Blur / Privacy Protector", "module": "photo", "credits_cost": 1, "is_novel": False},
    {"slug": "profile-picture-styler", "name": "AI Profile Picture Styler", "module": "photo", "credits_cost": 2, "is_novel": False},
    {"slug": "deepfake-detector", "name": "Deepfake Detector", "module": "photo", "credits_cost": 3, "is_novel": True},
    # === Creator Studio ===
    {"slug": "thumbnail-analyzer", "name": "YouTube Thumbnail Analyzer", "module": "creator", "credits_cost": 2, "is_novel": False},
    {"slug": "caption-lens", "name": "Caption Lens", "module": "creator", "credits_cost": 1, "is_novel": False},
    {"slug": "meme-generator-pro", "name": "Meme Generator Pro", "module": "creator", "credits_cost": 1, "is_novel": False},
    {"slug": "video-thumbnail-extractor", "name": "Video Thumbnail Extractor", "module": "creator", "credits_cost": 1, "is_novel": False},
    {"slug": "pixelstory", "name": "PixelStory", "module": "creator", "credits_cost": 3, "is_novel": True},
    {"slug": "instagram-feed-scorer", "name": "Instagram Feed Scorer", "module": "creator", "credits_cost": 2, "is_novel": False},
    {"slug": "outfit-feedback-engine", "name": "Outfit Feedback Engine", "module": "creator", "credits_cost": 2, "is_novel": False},
    # === Business Intelligence ===
    {"slug": "shelf-counter", "name": "Shelf Product Counter", "module": "business", "credits_cost": 2, "is_novel": False},
    {"slug": "queue-analyzer", "name": "Queue Length Analyzer", "module": "business", "credits_cost": 2, "is_novel": False},
    {"slug": "vehicle-counter", "name": "Vehicle Counter", "module": "business", "credits_cost": 2, "is_novel": False},
    {"slug": "parking-space-counter", "name": "Parking Space Counter", "module": "business", "credits_cost": 2, "is_novel": False},
    {"slug": "crowd-density", "name": "Crowd Density Estimator", "module": "business", "credits_cost": 2, "is_novel": False},
    {"slug": "crowdmood", "name": "CrowdMood™ Analyzer", "module": "business", "credits_cost": 3, "is_novel": True},
    {"slug": "ppe-safety-checker", "name": "PPE Safety Checker", "module": "business", "credits_cost": 2, "is_novel": False},
    {"slug": "face-attendance", "name": "Face Attendance System", "module": "business", "credits_cost": 2, "is_novel": False},
    # === Agriculture AI ===
    {"slug": "plant-disease-detector", "name": "Plant Disease Detector", "module": "agriculture", "credits_cost": 2, "is_novel": False},
    {"slug": "crop-health-monitor", "name": "Crop Health Monitor", "module": "agriculture", "credits_cost": 2, "is_novel": False},
    {"slug": "harvest-readiness", "name": "Harvest Readiness Scorer", "module": "agriculture", "credits_cost": 2, "is_novel": False},
    {"slug": "weed-analyzer", "name": "Weed Density Analyzer", "module": "agriculture", "credits_cost": 2, "is_novel": False},
    {"slug": "irrigation-stress", "name": "Irrigation Stress Detector", "module": "agriculture", "credits_cost": 2, "is_novel": False},
    {"slug": "soil-color-analyzer", "name": "Soil Color Analyzer", "module": "agriculture", "credits_cost": 2, "is_novel": False},
    # === Entertainment ===
    {"slug": "age-predictor", "name": "Age Predictor", "module": "entertainment", "credits_cost": 1, "is_novel": False},
    {"slug": "celebrity-lookalike", "name": "Celebrity Look-alike", "module": "entertainment", "credits_cost": 2, "is_novel": False},
    {"slug": "cartoon-avatar", "name": "Cartoon Avatar Generator", "module": "entertainment", "credits_cost": 2, "is_novel": False},
    {"slug": "pet-breed-detector", "name": "Pet Breed Detector", "module": "entertainment", "credits_cost": 1, "is_novel": False},
    {"slug": "emotion-mirror", "name": "Emotion Mirror", "module": "entertainment", "credits_cost": 1, "is_novel": False},
    {"slug": "vibe-check", "name": "Vibe Check", "module": "entertainment", "credits_cost": 2, "is_novel": True},
    {"slug": "body-comparison", "name": "Body Composition Analyzer", "module": "entertainment", "credits_cost": 2, "is_novel": False},
]

if __name__ == "__main__":
    print(f"Total tools: {len(TOOLS)}")
    for t in TOOLS:
        print(f"  - [{t['module']:15}] {t['slug']}")
