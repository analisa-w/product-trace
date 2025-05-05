from block import Block

class Blockchain:
    def __init__(self):
        """Constructor for the Blockchain class"""
        self.chain = [self.create_genesis_block()]
        self.forks = {}  # Store potential fork chains, keyed by their head block hash
        self.pending_transactions = []  # Store transactions before they're added to a block

    def create_genesis_block(self):
        """Creates initial block, or block 0, to initialize the blockchain"""
        genesis = Block(0, "0" * 64, [])
        genesis.mine_block()  # Mine the genesis block
        return genesis

    def is_product_registered(self, serial_number):
        """Check if a product is already registered in the blockchain"""
        for block in self.chain:
            for tx in block.transactions:
                if tx["type"] == "register" and tx["serial_number"] == serial_number:
                    return True
        return False

    def add_transaction(self, transaction):
        """Add a transaction to the pending transactions list"""
        self.pending_transactions.append(transaction)
        return True

    def mine_block(self):
        """Mine a new block with the pending transactions"""
        if not self.pending_transactions:
            return None

        last_block = self.chain[-1]
        new_block = Block(
            last_block.index + 1,
            last_block.hash,
            self.pending_transactions.copy()
        )

        # Mine the block (find nonce that satisfies difficulty)
        new_block.mine_block()
        
        # Clear pending transactions
        self.pending_transactions = []
        
        return new_block

    def add_block(self, block):
        """Add a new block to the chain"""
        if self.is_valid_block(block):
            self.chain.append(block)
            return True
        return False

    def is_valid_block(self, block):
        """Check if a block is valid"""
        # Check if block's hash is valid
        if not block.is_valid():
            print(f"Malicious block detected & blocked (invalid hash): {block.hash}")
            return False
            
        # Check if block's hash meets difficulty requirement
        if not block.hash.startswith("0" * 4):  # Difficulty of 4
            print(f"Block difficulty check failed for block {block.hash}")
            return False
            
        return True

    def is_valid_chain(self, chain=None):
        """Check if a chain is valid"""
        if chain is None:
            chain = self.chain
            
        # Check genesis block - only check for valid hash and difficulty, not the exact index or prev_hash
        # This allows nodes to have different genesis blocks
        if not chain[0].is_valid() or not chain[0].hash.startswith("0" * 4):
            print("Invalid genesis block")
            return False
            
        # Check each block
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i-1]
            
            if not current.is_valid():
                print(f"Block {current.hash} failed validation")
                return False
                
            if current.prev_hash != previous.hash:
                print(f"Block {current.hash} prev_hash doesn't match previous block's hash")
                return False
                
            # Check if block's hash meets difficulty requirement
            if not current.hash.startswith("0" * 4):  # Difficulty of 4
                print(f"Block {current.hash} doesn't meet difficulty requirement")
                return False
                
        return True

    def add_fork(self, block):
        """Add a valid fork block to the forks dictionary"""
        # First check if this is a block we already have in our main chain
        for existing_block in self.chain:
            if existing_block.hash == block.hash:
                print(f"Block {block.hash} already in main chain")
                return True
                
        # Then check if it's already in a fork chain
        for fork_chain in self.forks.values():
            for existing_block in fork_chain:
                if existing_block.hash == block.hash:
                    print(f"Block {block.hash} already in a fork chain")
                    return True

        # Now check if the block is valid
        if not self.is_valid_block(block):
            print(f"Block validation failed for block {block.hash}")
            return False
            
        # If this is a new fork chain
        if block.hash not in self.forks:
            self.forks[block.hash] = [block]
            print(f"Created new fork chain with block {block.hash}")
            
            # Try to build the fork chain by finding previous blocks
            current = block
            while current.prev_hash != "0" * 64:  # Stop when we reach a genesis block
                found = False
                # Check main chain
                for existing_block in self.chain:
                    if existing_block.hash == current.prev_hash:
                        self.forks[block.hash].append(existing_block)
                        current = existing_block
                        found = True
                        print(f"Found previous block {current.hash} in main chain")
                        break
                # Check other fork chains
                if not found:
                    for fork_chain in self.forks.values():
                        for existing_block in fork_chain:
                            if existing_block.hash == current.prev_hash:
                                self.forks[block.hash].append(existing_block)
                                current = existing_block
                                found = True
                                print(f"Found previous block {current.hash} in fork chain")
                                break
                        if found:
                            break
                if not found:
                    # We're missing some blocks in this fork chain
                    print(f"Missing block with hash {current.prev_hash}")
                    return True
        else:
            # Add block to existing fork chain if not already there
            if block not in self.forks[block.hash]:
                self.forks[block.hash].append(block)
                print(f"Added block {block.hash} to fork chain")
                    
        return True

    def resolve_forks(self):
        """Resolve forks by selecting the longest valid chain"""
        if not self.forks:
            return False
            
        print(f"Resolving forks. Current chain length: {len(self.chain)}")
        # Find the longest valid chain among forks
        longest_chain = self.chain
        for fork_head_hash, fork_chain in list(self.forks.items()):
            print(f"Checking fork chain with length {len(fork_chain)}")
            # Sort the fork chain by index to ensure it's in the right order
            fork_chain.sort(key=lambda block: block.index)
            
            # Check if this fork chain is longer and valid
            if len(fork_chain) > len(longest_chain) and self.is_valid_chain(fork_chain):
                print(f"Found longer valid chain with length {len(fork_chain)}")
                longest_chain = fork_chain.copy()
            # If chains are same length, prefer the one with more transactions
            elif len(fork_chain) == len(longest_chain) and self.is_valid_chain(fork_chain):
                fork_tx_count = sum(len(block.transactions) for block in fork_chain)
                current_tx_count = sum(len(block.transactions) for block in longest_chain)
                if fork_tx_count > current_tx_count:
                    print(f"Found chain with more transactions: {fork_tx_count} vs {current_tx_count}")
                    longest_chain = fork_chain.copy()
                
        # If we found a longer chain, switch to it
        if longest_chain != self.chain:
            print(f"Switching to new chain with length {len(longest_chain)}")
            self.chain = longest_chain
            self.forks = {}  # Clear forks after resolution
            return True
            
        return False

    def get_missing_blocks(self, fork_hash):
        """Get a list of missing block hashes needed to complete a fork chain"""
        if fork_hash not in self.forks:
            return []
            
        fork_chain = self.forks[fork_hash]
        missing_hashes = []
        current = fork_chain[-1]  # Start from the oldest block in the fork
        
        # Find missing blocks between fork and main chain
        while current.prev_hash != self.chain[-1].hash:
            found = False
            # Check main chain
            for block in self.chain:
                if block.hash == current.prev_hash:
                    found = True
                    current = block
                    break
            # Check other fork chains
            if not found:
                for other_fork_chain in self.forks.values():
                    for block in other_fork_chain:
                        if block.hash == current.prev_hash:
                            found = True
                            current = block
                            break
                    if found:
                        break
            if not found:
                missing_hashes.append(current.prev_hash)
                break
                
        return missing_hashes

    def verify_product(self, serial_number):
        """Verify a product's status in the blockchain"""
        result = {
            "registered": False,
            "owner": None,
            "history": []
        }
        
        # Check both main chain and fork chains
        chains_to_check = [self.chain] + list(self.forks.values())
        
        for chain in chains_to_check:
            for block in chain:
                for tx in block.transactions:
                    if tx["serial_number"] == serial_number:
                        if tx["type"] == "register":
                            result["registered"] = True
                            result["owner"] = tx["owner"]
                            result["history"].append(f"Registered by {tx['owner']}")
                        elif tx["type"] == "transfer":
                            result["owner"] = tx["to"]
                            result["history"].append(f"Transferred from {tx['from']} to {tx['to']}")
                        
        return result
