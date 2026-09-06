// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FaceProvenanceVerifier
 * @notice Verifies biometric face similarity on-chain via bitwise Hamming distance 
 *         and immutably anchors tamper-evident provenance manifests.
 * @dev Designed for HackerHouse Goa 2026 - Task 3 (Face Identification & Blockchain Verification)
 */
contract FaceProvenanceVerifier {

    // --- Data Structures ---

    struct ProvenanceRecord {
        bytes32 proofId;               // Unique cryptographic proof identifier
        bytes32 inputFingerprint;      // 256-bit quantized biometric vector of the input scan
        bytes32 discoveredFingerprint; // 256-bit quantized biometric vector of discovered social media face
        bytes32 metadataDigest;        // Keccak-256 hash of social post metadata (URL, Author, Timestamp, etc.)
        uint8 hammingDistance;         // On-chain computed bitwise distance between the two faces
        uint256 blockTimestamp;        // Immutable blockchain timestamp
        address verifier;              // Address of the submitter/oracle
        string sourceUrl;              // Canonical URL of discovered social media post
        bool isRevoked;                // Flag for governance / invalidation
    }

    // --- State Variables ---

    address public owner;
    uint8 public maxHammingTolerance = 35; // Default max allowed bit differences for biometric match (out of 256 bits)
    uint256 public totalProofsCount;

    // Mapping: proofId => ProvenanceRecord
    mapping(bytes32 => ProvenanceRecord) private proofs;

    // Mapping: metadataDigest => proofId (prevents duplicate anchoring)
    mapping(bytes32 => bytes32) public digestToProof;

    // --- Events ---

    event ProofAnchored(
        bytes32 indexed proofId,
        bytes32 indexed metadataDigest,
        uint8 hammingDistance,
        uint256 timestamp,
        address indexed verifier,
        string sourceUrl
    );

    event ProofRevoked(bytes32 indexed proofId, address indexed revoker);
    event ToleranceUpdated(uint8 oldTolerance, uint8 newTolerance);

    // --- Modifiers ---

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    // --- Constructor ---

    constructor() {
        owner = msg.sender;
    }

    // --- External / Public Functions ---

    /**
     * @notice Computes bitwise Hamming distance between two 256-bit biometric vectors on-chain
     *         and immutably records the provenance manifest if distance is within tolerance.
     * @param inputFingerprint 256-bit binary fingerprint of the query face
     * @param discoveredFingerprint 256-bit binary fingerprint of the discovered social media face
     * @param metadataDigest Keccak-256 hash of the complete post manifest
     * @param sourceUrl URL of the discovered post
     * @return proofId The unique on-chain identifier for this proof
     */
    function verifyAndAnchor(
        bytes32 inputFingerprint,
        bytes32 discoveredFingerprint,
        bytes32 metadataDigest,
        string calldata sourceUrl
    ) external returns (bytes32 proofId) {
        require(bytes(sourceUrl).length > 0, "Source URL cannot be empty");
        require(metadataDigest != bytes32(0), "Metadata digest cannot be null");
        require(digestToProof[metadataDigest] == bytes32(0), "Proof for this metadata already anchored");

        // 1. Calculate on-chain Bitwise Hamming Distance (XOR + popcount)
        uint8 distance = computeHammingDistance(inputFingerprint, discoveredFingerprint);

        // 2. Enforce biometric match threshold on-chain
        require(distance <= maxHammingTolerance, "Biometric match rejected: Hamming distance exceeds tolerance");

        // 3. Generate unique deterministic proofId
        proofId = keccak256(
            abi.encodePacked(
                inputFingerprint,
                discoveredFingerprint,
                metadataDigest,
                block.timestamp,
                msg.sender
            )
        );

        // 4. Store Provenance Record
        proofs[proofId] = ProvenanceRecord({
            proofId: proofId,
            inputFingerprint: inputFingerprint,
            discoveredFingerprint: discoveredFingerprint,
            metadataDigest: metadataDigest,
            hammingDistance: distance,
            blockTimestamp: block.timestamp,
            verifier: msg.sender,
            sourceUrl: sourceUrl,
            isRevoked: false
        });

        digestToProof[metadataDigest] = proofId;
        totalProofsCount++;

        // 5. Emit indexable verification event
        emit ProofAnchored(
            proofId,
            metadataDigest,
            distance,
            block.timestamp,
            msg.sender,
            sourceUrl
        );

        return proofId;
    }

    /**
     * @notice Verifies whether a given metadata digest matches the on-chain recorded proof.
     * @param proofId Unique proof identifier
     * @param testMetadataDigest Candidate metadata digest to test
     * @return isValid True if proof exists, is not revoked, and digest matches exactly
     * @return distance The recorded on-chain Hamming distance
     * @return timestamp Block timestamp when the proof was anchored
     * @return sourceUrl The recorded source URL
     */
    function verifyProof(
        bytes32 proofId,
        bytes32 testMetadataDigest
    ) external view returns (
        bool isValid,
        uint8 distance,
        uint256 timestamp,
        string memory sourceUrl
    ) {
        ProvenanceRecord memory record = proofs[proofId];
        
        if (record.proofId == bytes32(0) || record.isRevoked) {
            return (false, 0, 0, "");
        }

        bool digestMatches = (record.metadataDigest == testMetadataDigest);
        return (
            digestMatches,
            record.hammingDistance,
            record.blockTimestamp,
            record.sourceUrl
        );
    }

    /**
     * @notice Retrieves the full record details of an anchored proof.
     */
    function getProof(bytes32 proofId) external view returns (ProvenanceRecord memory) {
        require(proofs[proofId].proofId != bytes32(0), "Proof does not exist");
        return proofs[proofId];
    }

    /**
     * @notice Helper to calculate the Hamming Distance (differing bits) between two 256-bit hashes.
     */
    function computeHammingDistance(bytes32 a, bytes32 b) public pure returns (uint8) {
        bytes32 diff = a ^ b; // Bitwise XOR: 1 where bits differ
        uint256 v = uint256(diff);
        
        // Fast popcount (count set bits) in uint256
        uint256 count = 0;
        while (v != 0) {
            v &= (v - 1); // Clears the lowest set bit
            count++;
        }
        return uint8(count);
    }

    // --- Admin / Governance Functions ---

    function setMaxHammingTolerance(uint8 newTolerance) external onlyOwner {
        require(newTolerance <= 128, "Tolerance too loose");
        emit ToleranceUpdated(maxHammingTolerance, newTolerance);
        maxHammingTolerance = newTolerance;
    }

    function revokeProof(bytes32 proofId) external onlyOwner {
        require(proofs[proofId].proofId != bytes32(0), "Proof does not exist");
        proofs[proofId].isRevoked = true;
        emit ProofRevoked(proofId, msg.sender);
    }
}
