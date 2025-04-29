from block import Block

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    '''def create_genesis_block(self):
        genesis_block = Block(0, "0", [])
        self.chain.append(genesis_block)'''
    
    def create_genesis_block(self):
        genesis_block = Block(0, "0", [])
        genesis_block.timestamp = 0  # Force timestamp to 0
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)


    def add_block(self, transactions):
        last_block = self.chain[-1]
        new_block = Block(len(self.chain), last_block.hash, transactions)
        mined_block = self.mine_block(new_block)
        self.chain.append(mined_block)

    def mine_block(self, block, difficulty=3):
        block.nonce = 0
        while not block.compute_hash().startswith('0' * difficulty):
            block.nonce += 1
        block.hash = block.compute_hash()
        return block

    def is_valid_chain(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            if current.prev_hash != previous.hash:
                return False
            if not current.hash.startswith('0' * 3):
                return False
            if current.hash != current.compute_hash():
                return False
        return True


    def verify_product(self, serial_number):
        history = []
        current_owner = None
        found = False

        for block in self.chain:
            for tx in block.transactions:
                if tx.get("serial_number") == serial_number:
                    found = True
                    if tx["type"] == "register":
                        current_owner = tx["owner"]
                        history.append(f"Registered by {tx['owner']} as model {tx['model']}")
                    elif tx["type"] == "transfer":
                        current_owner = tx["to"]
                        history.append(f"Transferred from {tx['from']} to {tx['to']}")

        if not found:
            return {
                "registered": False,
                "owner": None,
                "history": []
            }

        return {
            "registered": True,
            "owner": current_owner,
            "history": history
        }
