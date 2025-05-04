import hashlib
import json
import time

class Block:
    def __init__(self, index, prev_hash, transactions, nonce=0, hash=None, timestamp=None):
        self.index = index
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.prev_hash = prev_hash
        self.transactions = transactions  # list of dicts
        self.nonce = nonce
        self.hash = hash if hash is not None else self.compute_hash()

    def compute_hash(self):
        block_content = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "transactions": self.transactions,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_content).hexdigest()

    def mine_block(self, difficulty=4):
        """Mine the block by finding a nonce that satisfies the difficulty"""
        while True:
            self.hash = self.compute_hash()
            if self.hash.startswith("0" * difficulty):
                break
            self.nonce += 1

    def is_valid(self):
        """Check if the block's hash is valid"""
        return self.hash == self.compute_hash()
