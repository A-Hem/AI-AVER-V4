"""
Evidence chain of custody and verification
"""
from datetime import datetime
from typing import Dict, List
import hashlib
import json
import sqlite3
from pathlib import Path

class EvidenceChain:
    """Manage evidence chain of custody"""
    
    def __init__(self, db_path: str = "evidence_chain.db"):
        self.db_path = db_path
        self._init_database()
    
    def add_evidence(self, file_path: str, source: str, handler: str) -> str:
        """Add new evidence to chain"""
        evidence_id = self._generate_evidence_id(file_path)
        
        evidence_record = {
            'evidence_id': evidence_id,
            'file_path': file_path,
            'source': source,
            'handler': handler,
            'timestamp': datetime.now().isoformat(),
            'hash_sha256': self._calculate_file_hash(file_path),
            'file_size': Path(file_path).stat().st_size,
            'status': 'acquired'
        }
        
        self._insert_evidence_record(evidence_record)
        return evidence_id
    
    def verify_evidence_integrity(self, evidence_id: str) -> Dict:
        """Verify evidence hasn't been tampered with"""
        record = self._get_evidence_record(evidence_id)
        if not record:
            return {'status': 'error', 'message': 'Evidence not found'}
        
        current_hash = self._calculate_file_hash(record['file_path'])
        original_hash = record['hash_sha256']
        
        integrity_check = {
            'evidence_id': evidence_id,
            'integrity_verified': current_hash == original_hash,
            'original_hash': original_hash,
            'current_hash': current_hash,
            'verification_time': datetime.now().isoformat()
        }
        
        self._log_verification(integrity_check)
        return integrity_check
