import hashlib
import json
import time

class Block:
    def __init__(self, index, prev_hash, transactions):
        self.index = index
        self.timestamp = time.time()
        self.prev_hash = prev_hash
        self.transactions = transactions  # list of dicts
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_content = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "transactions": self.transactions,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_content).hexdigest()
