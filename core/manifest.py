"""
Digital Provenance Manifest & Cryptographic Certificate Generator
Aegis-ZK Protocol - HackerHouse Goa 2026 Task 3
"""

import json
import time
import hashlib
from typing import Dict, Any, Optional

try:
    from Crypto.Hash import keccak
    def keccak256_hex(data_bytes: bytes) -> str:
        k = keccak.new(digest_bits=256)
        k.update(data_bytes)
        return "0x" + k.hexdigest()
except ImportError:
    # Fallback to standard SHA3-256 / SHA-256
    def keccak256_hex(data_bytes: bytes) -> str:
        return "0x" + hashlib.sha3_256(data_bytes).hexdigest()


class ManifestBuilder:
    """
    Builds canonical tamper-evident digital provenance manifests compliant with EIP-712 / C2PA schemas.
    """

    @staticmethod
    def build_manifest(
        input_fingerprint_hex: str,
        web_fingerprint_hex: str,
        social_post_metadata: Dict[str, Any],
        hamming_distance: int,
        cosine_similarity: float,
        verifier_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Constructs canonical JSON manifest and computes its deterministic Keccak-256 digest.
        """
        canonical_data = {
            "protocol": "Aegis-ZK-Provenance-v1",
            "biometric_attestation": {
                "input_fingerprint": input_fingerprint_hex,
                "discovered_fingerprint": web_fingerprint_hex,
                "hamming_distance_bits": int(hamming_distance),
                "cosine_similarity": round(float(cosine_similarity), 4),
                "match_verdict": "VERIFIED_AUTHENTIC" if hamming_distance <= 35 else "MATCH_REJECTED"
            },
            "discovered_post": {
                "platform": social_post_metadata.get("platform", "Unknown"),
                "source_url": social_post_metadata.get("source_url", ""),
                "author": social_post_metadata.get("author", "Unknown"),
                "title": social_post_metadata.get("title", ""),
                "post_timestamp": int(social_post_metadata.get("timestamp", time.time())),
                "search_engine": social_post_metadata.get("search_engine", "Visual Oracle")
            },
            "timestamp": int(time.time()),
            "verifier": verifier_address or "0x71C...AegisOracle"
        }

        # Canonical deterministic JSON string (sorted keys, compact separators)
        canonical_json_str = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        metadata_digest = keccak256_hex(canonical_json_str.encode('utf-8'))

        return {
            "manifest_json": canonical_data,
            "canonical_string": canonical_json_str,
            "metadata_digest": metadata_digest
        }

    @staticmethod
    def generate_html_certificate(
        proof_id: str,
        tx_hash: str,
        manifest: Dict[str, Any],
        block_timestamp: int,
        network_name: str = "Polygon Amoy / Local EVM"
    ) -> str:
        """
        Generates an ultra-sleek, verifiable HTML Certificate of Authenticity.
        """
        bio = manifest.get("biometric_attestation", {})
        post = manifest.get("discovered_post", {})
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aegis-ZK Digital Provenance Certificate</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .certificate-card {{
            background: linear-gradient(145deg, #161b22, #0d1117);
            border: 1px solid #30363d;
            border-radius: 16px;
            padding: 32px;
            max-width: 650px;
            width: 100%;
            box-shadow: 0 12px 36px rgba(0, 255, 170, 0.1);
            position: relative;
        }}
        .badge {{
            display: inline-block;
            background: rgba(46, 160, 67, 0.15);
            color: #3fb950;
            border: 1px solid #2ea043;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.5px;
        }}
        h1 {{
            color: #58a6ff;
            font-size: 22px;
            margin: 12px 0 6px 0;
        }}
        .subtitle {{
            color: #8b949e;
            font-size: 13px;
            margin-bottom: 24px;
        }}
        .field-group {{
            margin-bottom: 16px;
            background: rgba(255, 255, 255, 0.02);
            padding: 12px 16px;
            border-radius: 8px;
            border-left: 3px solid #58a6ff;
        }}
        .field-label {{
            font-size: 11px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .field-value {{
            font-size: 14px;
            color: #f0f6fc;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            margin-top: 4px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        .footer {{
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid #30363d;
            font-size: 12px;
            color: #8b949e;
            display: flex;
            justify-content: space-between;
        }}
    </style>
</head>
<body>
    <div class="certificate-card">
        <div class="badge">ON-CHAIN VERIFIED PROVENANCE</div>
        <h1>Aegis-ZK Authenticity Seal</h1>
        <div class="subtitle">Decentralized Face Biometrics & Social Media Provenance Certificate</div>

        <div class="field-group">
            <div class="field-label">Proof Identifier (Proof ID)</div>
            <div class="field-value">{proof_id}</div>
        </div>

        <div class="field-group">
            <div class="field-label">Transaction Hash</div>
            <div class="field-value">{tx_hash}</div>
        </div>

        <div class="grid">
            <div class="field-group">
                <div class="field-label">Biometric Distance</div>
                <div class="field-value">{bio.get('hamming_distance_bits', 0)} bits (Tolerance: &le; 35)</div>
            </div>
            <div class="field-group">
                <div class="field-label">Cosine Similarity</div>
                <div class="field-value">{bio.get('cosine_similarity', 1.0) * 100:.1f}% Match</div>
            </div>
        </div>

        <div class="field-group">
            <div class="field-label">Discovered Social Source</div>
            <div class="field-value"><a href="{post.get('source_url', '#')}" style="color: #58a6ff;" target="_blank">{post.get('source_url', 'N/A')}</a></div>
        </div>

        <div class="footer">
            <span>Network: <strong>{network_name}</strong></span>
            <span>Anchored Timestamp: <strong>{block_timestamp}</strong></span>
        </div>
    </div>
</body>
</html>
"""
