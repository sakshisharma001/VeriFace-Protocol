"""
Automated Test Suite for Aegis-ZK Protocol
HackerHouse Goa 2026 - Shortlisting Task 3
"""

import os
import unittest
import numpy as np
from core.face_engine import FaceEngine
from core.search_engine import SearchEngine
from core.blockchain_engine import BlockchainEngine, SimulatedEVMState
from core.manifest import ManifestBuilder


class TestAegisZKPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.face_engine = FaceEngine()
        cls.search_engine = SearchEngine()
        cls.blockchain_engine = BlockchainEngine()
        cls.sample_path = os.path.join(os.path.dirname(__file__), "test_samples", "elon_sample.jpg")

    def test_01_face_detection_and_quantization(self):
        """Test face detection, 512-d embeddings and 256-bit quantization"""
        res = self.face_engine.process_face(self.sample_path)
        
        self.assertIn("crop", res)
        self.assertEqual(res["crop"].shape, (160, 160, 3))
        self.assertEqual(len(res["embedding"]), 512)
        self.assertEqual(len(res["fingerprint_bytes"]), 32) # 256 bits = 32 bytes
        self.assertTrue(res["fingerprint_hex"].startswith("0x"))
        self.assertEqual(len(res["fingerprint_hex"]), 66)

    def test_02_hamming_distance_parity(self):
        """Test bitwise Hamming distance computation"""
        fp1 = bytes.fromhex("00" * 32)
        fp2 = bytes.fromhex("ff" + "00" * 31) # 8 bits difference
        
        dist = self.face_engine.compute_hamming_distance(fp1, fp2)
        self.assertEqual(dist, 8)
        
        # Test exact match
        self.assertEqual(self.face_engine.compute_hamming_distance(fp1, fp1), 0)

    def test_03_search_engine_discovery(self):
        """Test web/social media discovery engine"""
        face_crop = np.zeros((160, 160, 3), dtype=np.uint8)
        result = self.search_engine.search_face_on_web(face_crop, self.sample_path)
        
        self.assertIn("platform", result)
        self.assertIn("source_url", result)
        self.assertIn("title", result)
        self.assertTrue(result["source_url"].startswith("http"))

    def test_04_manifest_generation_and_hashing(self):
        """Test canonical manifest building and Keccak-256 digest"""
        fp_hex = "0x" + "11" * 32
        social_meta = {
            "platform": "X (Twitter)",
            "source_url": "https://x.com/test/status/123",
            "author": "@test",
            "title": "Test Post",
            "timestamp": 1700000000
        }
        manifest = ManifestBuilder.build_manifest(
            input_fingerprint_hex=fp_hex,
            web_fingerprint_hex=fp_hex,
            social_post_metadata=social_meta,
            hamming_distance=0,
            cosine_similarity=1.0
        )
        
        self.assertIn("metadata_digest", manifest)
        self.assertTrue(manifest["metadata_digest"].startswith("0x"))
        self.assertEqual(len(manifest["metadata_digest"]), 66)

    def test_05_blockchain_anchoring_and_tamper_rejection(self):
        """Test on-chain state machine and tamper detection"""
        evm = SimulatedEVMState()
        fp1 = "0x" + "11" * 32
        fp2 = "0x" + "11" * 32
        digest = "0x" + "aa" * 32
        url = "https://x.com/verified/status/123"

        # 1. Anchor record
        tx = evm.verify_and_anchor(fp1, fp2, digest, url)
        self.assertIn("proof_id", tx)
        self.assertTrue(tx["proof_id"].startswith("0x"))

        # 2. Verify with correct digest
        is_valid, dist, ts, rec_url = evm.verify_proof(tx["proof_id"], digest)
        self.assertTrue(is_valid)
        self.assertEqual(dist, 0)
        self.assertEqual(rec_url, url)

        # 3. Tamper test: Query with altered digest
        fake_digest = "0x" + "bb" * 32
        is_valid_fake, _, _, _ = evm.verify_proof(tx["proof_id"], fake_digest)
        self.assertFalse(is_valid_fake, "Blockchain must reject tampered digest!")


if __name__ == "__main__":
    unittest.main()
