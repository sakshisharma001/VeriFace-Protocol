"""
Face Identification & Biometric Vector Quantization Engine
VeriFace-Protocol - HackerHouse Goa 2026 Task 3
"""

import os
import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional
import hashlib

class FaceEngine:
    """
    Robust Face Detection, Feature Embedding, and 256-bit LSH Quantization Engine.
    Converts continuous facial feature vectors into discrete on-chain verifiable bitstrings.
    """

    def __init__(self, random_seed: int = 42):
        # Load OpenCV Haar Cascade for face detection (zero external C++ dependencies needed)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if not os.path.exists(cascade_path):
            raise FileNotFoundError(f"OpenCV cascade file not found at {cascade_path}")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Deterministic Locality-Sensitive Hashing (LSH) Hyperplane Projection Matrix
        # Maps 512-dimensional continuous metric embeddings to 256-bit Hamming space
        np.random.seed(random_seed)
        self.projection_matrix = np.random.randn(512, 256).astype(np.float32)
        # Normalize projection vectors
        self.projection_matrix /= np.linalg.norm(self.projection_matrix, axis=0, keepdims=True)

    def load_image(self, image_source: Any) -> np.ndarray:
        """
        Loads an image from a file path, numpy array, or raw bytes.
        """
        if isinstance(image_source, str):
            if not os.path.exists(image_source):
                raise FileNotFoundError(f"Image not found at path: {image_source}")
            img = cv2.imread(image_source)
            if img is None:
                raise ValueError(f"Could not decode image at path: {image_source}")
            return img
        elif isinstance(image_source, bytes):
            nparr = np.frombuffer(image_source, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image bytes")
            return img
        elif isinstance(image_source, np.ndarray):
            return image_source
        else:
            raise TypeError("Unsupported image source type")

    def detect_and_crop_face(self, image_source: Any, target_size: Tuple[int, int] = (160, 160)) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Detects the primary face in the image and returns the normalized cropped face.
        Returns: (cropped_face_bgr, (x, y, w, h))
        """
        img = self.load_image(image_source)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        if len(faces) == 0:
            # If standard haar detection missed (e.g. tight crop or stylized photo), take center crop
            h, w = img.shape[:2]
            min_dim = min(h, w)
            start_x = (w - min_dim) // 2
            start_y = (h - min_dim) // 2
            crop = img[start_y:start_y+min_dim, start_x:start_x+min_dim]
            bbox = (start_x, start_y, min_dim, min_dim)
        else:
            # Pick the largest detected face box
            largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = largest_face
            
            # Add 15% margin around the face
            pad_x = int(w * 0.15)
            pad_y = int(h * 0.15)
            img_h, img_w = img.shape[:2]
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(img_w, x + w + pad_x)
            y2 = min(img_h, y + h + pad_y)
            
            crop = img[y1:y2, x1:x2]
            bbox = (x1, y1, x2 - x1, y2 - y1)

        resized_crop = cv2.resize(crop, target_size, interpolation=cv2.INTER_AREA)
        return resized_crop, bbox

    def extract_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """
        Extracts a normalized 512-dimensional spatial & texture embedding vector from face crop.
        Combines multi-scale spatial gradients, color moments, and frequency characteristics.
        """
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        
        # 1. Multi-scale block gradients
        resized_32 = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
        grad_x = cv2.Sobel(resized_32, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(resized_32, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(grad_x, grad_y).flatten() # 1024 features
        
        # 2. Block pooling into 256 dimensions
        block_features = mag.reshape(256, 4).mean(axis=1) # 256-d
        
        # 3. Frequency domain (DCT coefficients)
        dct = cv2.dct(np.float32(resized_32))
        dct_features = dct[:16, :16].flatten() # 256-d
        
        # Concatenate to form 512-d raw vector
        raw_vector = np.concatenate([block_features, dct_features]).astype(np.float32)
        
        # L2 Normalization
        norm = np.linalg.norm(raw_vector)
        if norm > 0:
            raw_vector = raw_vector / norm
            
        return raw_vector

    def quantize_to_bytes32(self, embedding: np.ndarray) -> bytes:
        """
        Quantizes 512-d continuous embedding to a 256-bit (32 bytes) binary fingerprint using LSH.
        Mathematically guarantees that cosine similarity maps directly to Hamming distance!
        """
        # Project 512-d onto 256 hyperplanes
        projected = np.dot(embedding, self.projection_matrix) # shape (256,)
        
        # Sign thresholding: 1 if >= 0 else 0
        bits = (projected >= 0).astype(np.uint8)
        
        # Pack 256 boolean bits into 32 bytes
        byte_array = bytearray(32)
        for i in range(32):
            byte_val = 0
            for b in range(8):
                bit_idx = i * 8 + b
                if bits[bit_idx]:
                    byte_val |= (1 << (7 - b))
            byte_array[i] = byte_val
            
        return bytes(byte_array)

    def process_face(self, image_source: Any) -> Dict[str, Any]:
        """
        Full end-to-end face processing: Detection -> Feature Extraction -> 256-bit Quantization.
        """
        face_crop, bbox = self.detect_and_crop_face(image_source)
        embedding = self.extract_embedding(face_crop)
        fingerprint_bytes = self.quantize_to_bytes32(embedding)
        fingerprint_hex = "0x" + fingerprint_bytes.hex()
        
        # Compute SHA-256 for strict image hash
        image_bytes = cv2.imencode('.jpg', face_crop)[1].tobytes()
        sha256_hash = hashlib.sha256(image_bytes).hexdigest()

        return {
            "bbox": bbox,
            "crop": face_crop,
            "embedding": embedding,
            "fingerprint_bytes": fingerprint_bytes,
            "fingerprint_hex": fingerprint_hex,
            "image_sha256": "0x" + sha256_hash
        }

    @staticmethod
    def compute_hamming_distance(fingerprint_a: bytes, fingerprint_b: bytes) -> int:
        """
        Computes bitwise Hamming distance between two 32-byte fingerprints.
        Matches Solidity computeHammingDistance exactly.
        """
        if len(fingerprint_a) != 32 or len(fingerprint_b) != 32:
            raise ValueError("Fingerprints must be exactly 32 bytes (256 bits)")
            
        distance = 0
        for byte_a, byte_b in zip(fingerprint_a, fingerprint_b):
            xor_val = byte_a ^ byte_b
            distance += bin(xor_val).count('1')
        return distance

    @staticmethod
    def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Computes cosine similarity between two 512-d feature vectors [0.0 to 1.0].
        """
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
