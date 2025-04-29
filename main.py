from blockchain import Blockchain

if __name__ == "__main__":
    bc = Blockchain()

    tx1 = {"type": "register", "serial_number": "CHANEL123", "model": "Classic Flap", "owner": "Chanel"}
    bc.add_block([tx1])

    tx2 = {"type": "transfer", "serial_number": "CHANEL123", "from": "Chanel", "to": "Analisa"}
    bc.add_block([tx2])

    for block in bc.chain:
        print(f"\nBlock {block.index}")
        print(f"Hash: {block.hash}")
        print(f"Prev: {block.prev_hash}")
        print(f"Transactions: {block.transactions}")

    print("\n==== CHAIN VALIDITY BEFORE TAMPERING ====")
    print(bc.is_valid_chain())  # Should be True

    # Tamper with the chain manually
    ''' print("\n==== TAMPERING WITH THE CHAIN... ====")
    bc.chain[1].transactions[0]['owner'] = 'FakeBrand'

    # Recompute hash because the block changed (simulate a cheater trying to fake)
    bc.chain[1].hash = bc.chain[1].compute_hash()

    print("\n==== CHAIN VALIDITY AFTER TAMPERING ====")
    print(bc.is_valid_chain())  # Should now be False'''

    print("\n==== VERIFY PRODUCT TEST ====")
    result = bc.verify_product("CHANEL123")

    if result["registered"]:
        print(f"Current owner: {result['owner']}")
        print("Ownership history:")
        for record in result["history"]:
            print(f"- {record}")
    else:
        print("Product not registered.")

