"""
Utility to generate clean sample face images for demonstration and unit testing.
"""

import os
import cv2
import numpy as np

def create_sample_face(filepath: str, face_color=(180, 200, 230), seed=42):
    np.random.seed(seed)
    # 400x400 background
    img = np.ones((400, 400, 3), dtype=np.uint8) * 40
    
    # Head ellipse
    center = (200, 200)
    axes = (90, 120)
    cv2.ellipse(img, center, axes, 0, 0, 360, face_color, -1)
    cv2.ellipse(img, center, axes, 0, 0, 360, (100, 120, 150), 2)
    
    # Left eye
    cv2.circle(img, (165, 175), 14, (255, 255, 255), -1)
    cv2.circle(img, (165, 175), 6, (40, 40, 40), -1)
    
    # Right eye
    cv2.circle(img, (235, 175), 14, (255, 255, 255), -1)
    cv2.circle(img, (235, 175), 6, (40, 40, 40), -1)
    
    # Eyebrows
    cv2.line(img, (150, 155), (180, 155), (60, 40, 20), 3)
    cv2.line(img, (220, 155), (250, 155), (60, 40, 20), 3)
    
    # Nose
    pts = np.array([[200, 185], [193, 215], [207, 215]], np.int32)
    cv2.polylines(img, [pts], True, (120, 140, 170), 2)
    
    # Mouth
    cv2.ellipse(img, (200, 255), (35, 15), 0, 0, 180, (70, 70, 180), -1)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    cv2.imwrite(filepath, img)
    return filepath

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    f1 = create_sample_face(os.path.join(out_dir, "elon_sample.jpg"), face_color=(175, 195, 225), seed=10)
    f2 = create_sample_face(os.path.join(out_dir, "portrait_sample.jpg"), face_color=(190, 210, 240), seed=20)
    print(f"Sample face images created: {f1}, {f2}")
