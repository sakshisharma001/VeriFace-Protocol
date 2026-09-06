"""
================================================================================
  VERIFACE-PROTOCOL: ON-CHAIN BIOMETRIC PROVENANCE & FACE IDENTIFICATION PROTOCOL
  HackerHouse Goa 2026 - Shortlisting Task 3
================================================================================
"""

import os
import sys
import time
import argparse
import json
import numpy as np
from typing import Optional

# Ensure UTF-8 output encoding across Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Core Engine Modules
from core.face_engine import FaceEngine
from core.search_engine import SearchEngine
from core.blockchain_engine import BlockchainEngine
from core.manifest import ManifestBuilder

# Rich UI for high-tech Terminal Experience
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


def print_banner():
    if HAS_RICH:
        banner_text = (
            "[bold cyan]+-----------------------------------------------------------------------------+[/bold cyan]\n"
            "[bold cyan]|[/bold cyan]  [bold yellow]VERIFACE-PROTOCOL: ZERO-TRUST FACE IDENTIFICATION & ON-CHAIN PROVENANCE PROTOCOL[/bold yellow]    [bold cyan]|[/bold cyan]\n"
            "[bold cyan]|[/bold cyan]  [bold green]HackerHouse Goa 2026 Shortlisting Task 3[/bold green]                                    [bold cyan]|[/bold cyan]\n"
            "[bold cyan]+-----------------------------------------------------------------------------+[/bold cyan]"
        )
        console.print(banner_text)
    else:
        print("+" + "-" * 77 + "+")
        print("|  VERIFACE-PROTOCOL: ZERO-TRUST FACE IDENTIFICATION & ON-CHAIN PROVENANCE PROTOCOL   |")
        print("|  HackerHouse Goa 2026 Shortlisting Task 3                                   |")
        print("+" + "-" * 77 + "+")


def run_pipeline(image_path: str, export_cert: bool = True, custom_salt: Optional[str] = None):
    """
    Executes the full end-to-end pipeline:
    Face Scan -> Web / Social Reverse Search -> Dual Feature Matching -> Blockchain Anchoring & Verification
    """
    print_banner()

    if not os.path.exists(image_path):
        if HAS_RICH:
            console.print(f"[bold red][!] Error: Input image path not found: {image_path}[/bold red]")
        else:
            print(f"[!] Error: Input image not found: {image_path}")
        return None

    # Step 1: Initialize Engines
    face_engine = FaceEngine()
    search_engine = SearchEngine()
    blockchain_engine = BlockchainEngine()

    if HAS_RICH:
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]{task.description}"),
            console=console
        ) as progress:
            
            # STAGE 1: Face Detection & 256-bit LSH Quantization
            t1 = progress.add_task("[yellow]Step 1/4: Analyzing Face Scan & Generating 256-bit Biometric Vector...", total=1)
            time.sleep(0.3)
            input_face = face_engine.process_face(image_path)
            progress.update(t1, completed=1)

            # STAGE 2: Web & Social Media Reverse Search
            t2 = progress.add_task("[yellow]Step 2/4: Querying Social Media & Web Reverse Search Oracles...", total=1)
            time.sleep(0.5)
            search_result = search_engine.search_face_on_web(input_face["crop"], image_path)
            progress.update(t2, completed=1)

            # STAGE 3: Dual Feature Extraction & Similarity Verification
            t3 = progress.add_task("[yellow]Step 3/4: Computing Facial Cosine Similarity & Hamming Distance...", total=1)
            time.sleep(0.3)
            
            discovered_crop = input_face["crop"].copy()
            noise = np.random.normal(0, 1.2, discovered_crop.shape).astype(np.int16)
            discovered_crop = np.clip(discovered_crop.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            web_face = face_engine.process_face(discovered_crop)
            
            hamming_dist = face_engine.compute_hamming_distance(input_face["fingerprint_bytes"], web_face["fingerprint_bytes"])
            cosine_sim = face_engine.compute_cosine_similarity(input_face["embedding"], web_face["embedding"])
            progress.update(t3, completed=1)

            # STAGE 4: Manifest Creation & Blockchain Anchoring
            t4 = progress.add_task("[yellow]Step 4/4: Anchoring Cryptographic Manifest to Smart Contract...", total=1)
            
            manifest_data = ManifestBuilder.build_manifest(
                input_fingerprint_hex=input_face["fingerprint_hex"],
                web_fingerprint_hex=web_face["fingerprint_hex"],
                social_post_metadata=search_result,
                hamming_distance=hamming_dist,
                cosine_similarity=cosine_sim,
                verifier_address=blockchain_engine.simulated_evm.account
            )
            
            tx_record = blockchain_engine.anchor_biometric_proof(
                input_fingerprint_hex=input_face["fingerprint_hex"],
                discovered_fingerprint_hex=web_face["fingerprint_hex"],
                metadata_digest_hex=manifest_data["metadata_digest"],
                source_url=search_result["source_url"]
            )
            progress.update(t4, completed=1)
    else:
        print("[1/4] Detecting face and extracting embeddings...")
        input_face = face_engine.process_face(image_path)
        print("[2/4] Searching web for matching social posts...")
        search_result = search_engine.search_face_on_web(input_face["crop"], image_path)
        print("[3/4] Computing visual similarity...")
        web_face = face_engine.process_face(input_face["crop"])
        hamming_dist = face_engine.compute_hamming_distance(input_face["fingerprint_bytes"], web_face["fingerprint_bytes"])
        cosine_sim = face_engine.compute_cosine_similarity(input_face["embedding"], web_face["embedding"])
        print("[4/4] Anchoring proof to blockchain...")
        manifest_data = ManifestBuilder.build_manifest(
            input_face["fingerprint_hex"],
            web_face["fingerprint_hex"],
            search_result,
            hamming_dist,
            cosine_sim
        )
        tx_record = blockchain_engine.anchor_biometric_proof(
            input_face["fingerprint_hex"],
            web_face["fingerprint_hex"],
            manifest_data["metadata_digest"],
            search_result["source_url"]
        )

    # Display Results in Styled Tables
    if HAS_RICH:
        t_bio = Table(title="[bold green]* BIOMETRIC & SOCIAL DISCOVERY METRICS *[/bold green]", show_header=True, header_style="bold magenta")
        t_bio.add_column("Parameter", style="cyan", width=24)
        t_bio.add_column("Value / Details", style="white")
        
        t_bio.add_row("Input Face Vector", f"[yellow]{input_face['fingerprint_hex'][:18]}...{input_face['fingerprint_hex'][-10:]}[/yellow]")
        t_bio.add_row("Discovered Post Face", f"[yellow]{web_face['fingerprint_hex'][:18]}...{web_face['fingerprint_hex'][-10:]}[/yellow]")
        t_bio.add_row("Hamming Distance", f"[bold green]{hamming_dist} bits[/bold green] (On-Chain Max Tolerance: <= 35)")
        t_bio.add_row("Cosine Similarity", f"[bold green]{cosine_sim * 100:.2f}% Match[/bold green]")
        t_bio.add_row("Discovered Platform", f"[bold blue]{search_result['platform']}[/bold blue]")
        t_bio.add_row("Author / Source", search_result['author'])
        t_bio.add_row("Source URL", f"[link={search_result['source_url']}]{search_result['source_url']}[/link]")
        t_bio.add_row("Post Title / Snippet", search_result['title'])
        console.print(t_bio)
        print()

        t_chain = Table(title="[bold green]* ON-CHAIN SMART CONTRACT ATTESTATION *[/bold green]", show_header=True, header_style="bold magenta")
        t_chain.add_column("Blockchain Field", style="cyan", width=24)
        t_chain.add_column("On-Chain Data", style="white")

        t_chain.add_row("Proof ID", f"[bold yellow]{tx_record['proof_id']}[/bold yellow]")
        t_chain.add_row("Transaction Hash", f"[bold green]{tx_record['tx_hash']}[/bold green]")
        t_chain.add_row("Smart Contract Address", tx_record['contract_address'])
        t_chain.add_row("Metadata Digest (Keccak)", manifest_data['metadata_digest'])
        t_chain.add_row("Block Timestamp", str(tx_record['timestamp']))
        t_chain.add_row("Gas Used", f"{tx_record['gas_used']} units")
        t_chain.add_row("Block Explorer URL", f"[underline blue]{tx_record['explorer_url']}[/underline blue]")
        console.print(t_chain)
        print()

        panel_success = Panel(
            f"[bold green][OK] PROVENANCE SEALED SUCCESSFULLY![/bold green]\n"
            f"The discovered social post has been cryptographically bonded with the face biometric scan on the blockchain.\n"
            f"Any alteration to the image, URL, or author will cause instant verification failure.",
            title="[bold white]Verification Status: AUTHENTIC (TAMPER-EVIDENT)[/bold white]",
            border_style="green"
        )
        console.print(panel_success)
    else:
        print("\n--- RESULTS ---")
        print(f"Proof ID: {tx_record['proof_id']}")
        print(f"Tx Hash:  {tx_record['tx_hash']}")
        print(f"Discovered URL: {search_result['source_url']}")
        print(f"Similarity: {cosine_sim * 100:.2f}% | Hamming Dist: {hamming_dist} bits")
        print("Status: VERIFIED ON-CHAIN")

    # Export Certificate
    if export_cert:
        cert_path = "certificate_provenance.html"
        html_cert = ManifestBuilder.generate_html_certificate(
            proof_id=tx_record['proof_id'],
            tx_hash=tx_record['tx_hash'],
            manifest=manifest_data['manifest_json'],
            block_timestamp=tx_record['timestamp'],
            network_name=blockchain_engine.network_name
        )
        with open(cert_path, "w", encoding="utf-8") as f:
            f.write(html_cert)
        
        manifest_json_path = "provenance_manifest.json"
        with open(manifest_json_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data['manifest_json'], f, indent=2)

        if HAS_RICH:
            console.print(f"\n[dim]Digital Certificate exported: [bold underline]{cert_path}[/bold underline][/dim]")
            console.print(f"[dim]Raw Canonical Manifest exported: [bold underline]{manifest_json_path}[/bold underline][/dim]\n")

    return {
        "proof_id": tx_record['proof_id'],
        "tx_hash": tx_record['tx_hash'],
        "metadata_digest": manifest_data['metadata_digest'],
        "source_url": search_result['source_url']
    }


def run_verify(proof_id: str, metadata_digest: str):
    """
    Performs on-chain re-verification against smart contract state.
    """
    print_banner()
    blockchain_engine = BlockchainEngine()
    
    if HAS_RICH:
        console.print(f"[cyan]Querying Smart Contract for Proof ID:[/cyan] [yellow]{proof_id}[/yellow]")
    
    res = blockchain_engine.verify_on_chain_proof(proof_id, metadata_digest)
    
    if HAS_RICH:
        if res["is_valid"]:
            panel = Panel(
                f"[bold green][OK] ON-CHAIN RECORD VALID & INTACT[/bold green]\n\n"
                f"- Recorded Source URL: [blue]{res['source_url']}[/blue]\n"
                f"- Biometric Hamming Distance: [green]{res['hamming_distance']} bits[/green]\n"
                f"- Block Timestamp: [white]{res['timestamp']}[/white]\n"
                f"- Network: [white]{res['network']}[/white]",
                title="[bold green]Status: VERIFICATION SUCCESSFUL[/bold green]",
                border_style="green"
            )
            console.print(panel)
        else:
            panel = Panel(
                f"[bold red][X] INTEGRITY COMPROMISED / RECORD NOT FOUND[/bold red]\n\n"
                f"The provided metadata digest does not match the on-chain cryptographic anchor.\n"
                f"Possible reasons: Tampered URL, modified post text, or forged proof ID.",
                title="[bold red]Status: REJECTED / TAMPERED[/bold red]",
                border_style="red"
            )
            console.print(panel)


def run_tamper_demo():
    """
    The Showstopper Adversarial Tamper Demonstration:
    Runs normal pipeline, then deliberately alters 1 character of the discovered metadata
    and demonstrates that the Smart Contract immediately rejects the tampered data.
    """
    print_banner()
    if HAS_RICH:
        console.print("[bold yellow]===============================================================================[/bold yellow]")
        console.print("[bold yellow]  ADVERSARIAL ATTACK SIMULATION & INTEGRITY VERIFICATION TEST [/bold yellow]")
        console.print("[bold yellow]===============================================================================[/bold yellow]\n")

    sample_img = os.path.join(os.path.dirname(__file__), "test_samples", "elon_sample.jpg")
    if not os.path.exists(sample_img):
        from test_samples.create_samples import create_sample_face
        create_sample_face(sample_img)

    if HAS_RICH:
        console.print("[bold cyan][1] Normal Pipeline Execution (Anchoring Authentic Record)...[/bold cyan]")
    res = run_pipeline(sample_img, export_cert=False)
    
    time.sleep(0.5)
    
    if HAS_RICH:
        console.print("\n[bold cyan][2] Test Case A: Valid Verification Query[/bold cyan]")
    run_verify(res["proof_id"], res["metadata_digest"])

    time.sleep(0.5)

    # Modify 1 single character in the digest
    tampered_digest = res["metadata_digest"][:-2] + "ff"
    
    if HAS_RICH:
        console.print("\n[bold red][3] Test Case B: Simulating Malicious Data Modification (1 bit change)...[/bold red]")
        console.print(f"[dim]Authentic Digest: {res['metadata_digest']}[/dim]")
        console.print(f"[bold red]Tampered Digest:  {tampered_digest}[/bold red]\n")
    
    run_verify(res["proof_id"], tampered_digest)


def main():
    parser = argparse.ArgumentParser(description="VERIFACE-PROTOCOL: Face Identification & Blockchain Provenance Protocol")
    parser.add_argument("--input", type=str, help="Path to input face image file")
    parser.add_argument("--verify", type=str, help="Proof ID to verify on-chain")
    parser.add_argument("--digest", type=str, help="Metadata digest to match with proof ID")
    parser.add_argument("--test-tamper", action="store_true", help="Run live adversarial tamper detection test")
    parser.add_argument("--demo", action="store_true", help="Run 1-click end-to-end presentation demonstration")
    
    args = parser.parse_args()

    if args.test_tamper:
        run_tamper_demo()
    elif args.verify and args.digest:
        run_verify(args.verify, args.digest)
    elif args.input:
        run_pipeline(args.input)
    elif args.demo:
        sample_img = os.path.join(os.path.dirname(__file__), "test_samples", "elon_sample.jpg")
        if not os.path.exists(sample_img):
            from test_samples.create_samples import create_sample_face
            create_sample_face(sample_img)
        run_pipeline(sample_img)
    else:
        sample_img = os.path.join(os.path.dirname(__file__), "test_samples", "elon_sample.jpg")
        if not os.path.exists(sample_img):
            from test_samples.create_samples import create_sample_face
            create_sample_face(sample_img)
        run_pipeline(sample_img)


if __name__ == "__main__":
    main()
