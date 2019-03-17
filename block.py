import hashlib
import json
import blockchain
import transaction


class Block:

    def __init__(self, nonce, timestamp, transactions, previous_hash):
        self.nonce = nonce
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
