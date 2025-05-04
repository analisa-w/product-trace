import socket
import sys
import json
from blockchain import Blockchain
from block import Block


def start_node(my_port):
    # Create peer list based on the current port
    base_port = (my_port // 1000) * 1000  # Get the base port (5000, 6000, etc.)
    peer_list = []
    
    # Add peers in the same range
    for port in range(base_port + 1, base_port + 4):
        if port != my_port:  # Don't add self as peer
            peer_list.append(("127.0.0.1", port))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", my_port))
    print(f"Node is running and listening on port {my_port}...")
    print(f"Peers: {peer_list}")

    bc = Blockchain()

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            message = json.loads(data.decode())
            print(f"Parsed JSON message: {message}")

            if message.get("status") == "success" and "chain" in message:
                print("Received blockchain data in response to get_blockchain request")
                # Process blockchain from another node
                chain_data = message["chain"]
                
                # Convert JSON data to Block objects
                new_chain = []
                for block_data in chain_data:
                    new_block = Block(
                        block_data["index"],
                        block_data["prev_hash"],
                        block_data["transactions"],
                        block_data["nonce"],
                        block_data["hash"],
                        block_data["timestamp"]
                    )
                    new_chain.append(new_block)
                
                # Check if this chain is valid and longer than our current chain
                if len(new_chain) > len(bc.chain) and bc.is_valid_chain(new_chain):
                    print(f"Received valid blockchain with length {len(new_chain)} (current: {len(bc.chain)})")
                    bc.chain = new_chain
                    print("Switched to received blockchain")
                    # Clear any forks
                    bc.forks = {}
                    # Broadcast the new chain to ensure consistency
                    for block in bc.chain:
                        broadcast_block(sock, block, peer_list)
                else:
                    print(f"Received blockchain not adopted: length {len(new_chain)} (current: {len(bc.chain)})")
            
            elif message["type"] == "register":
                print("Received a register request!")
                serial = message["data"]["serial_number"]
                model = message["data"]["model"]
                brand = message["data"]["brand"]

                # Check if product already exists
                if bc.is_product_registered(serial):
                    print(f"Registration rejected, product {serial} already exists")
                    response = {"status": "rejected", "reason": "Product with that serial number already exists."}
                    sock.sendto(json.dumps(response).encode(), addr)
                    continue

                # Create transaction
                tx = {
                    "type": "register",
                    "serial_number": serial,
                    "model": model,
                    "owner": brand
                }

                # Add transaction to blockchain
                bc.add_transaction(tx)
                new_block = bc.mine_block()
                if new_block:
                    bc.add_block(new_block)
                    print(f"Broadcasted new block to {addr[0]}:{addr[1]}")
                    broadcast_block(sock, new_block, peer_list)

                response = {"status": "accepted"}
                sock.sendto(json.dumps(response).encode(), addr)

            elif message["type"] == "transfer":
                print("Received a transfer request!")
                serial = message["data"]["serial_number"]
                from_owner = message["data"]["from"]
                to_owner = message["data"]["to"]

                result = bc.verify_product(serial)

                response = {}

                if not result["registered"]:
                    print(f"Transfer rejected: Product {serial} not registered.")
                    response = {"status": "rejected", "reason": "Product not registered."}
                elif result["owner"] != from_owner:
                    print(f"Transfer rejected: {from_owner} is not the current owner.")
                    response = {"status": "rejected", "reason": "Wrong current owner."}
                else:
                    tx = {
                        "type": "transfer",
                        "serial_number": serial,
                        "from": from_owner,
                        "to": to_owner
                    }
                    bc.add_transaction(tx)
                    new_block = bc.mine_block()
                    if new_block:
                        bc.add_block(new_block)
                        broadcast_block(sock, new_block, peer_list)

                    print(f"Transferred product: {tx}")
                    broadcast_block(sock, bc.chain[-1], peer_list)
                    response = {"status": "accepted"}

                # ✅ Send a response back to sender
                sock.sendto(json.dumps(response).encode(), addr)

            elif message["type"] == "verify":
                print("Received a verification request!")
                serial = message["data"]["serial_number"]

                result = bc.verify_product(serial)

                if result["registered"]:
                    # Build history from the blockchain
                    history = []
                    for block in bc.chain:
                        for tx in block.transactions:
                            if tx["serial_number"] == serial:
                                if tx["type"] == "register":
                                    history.append(f"Registered by {tx['owner']}")
                                elif tx["type"] == "transfer":
                                    history.append(f"Transferred from {tx['from']} to {tx['to']}")

                    response = {
                        "registered": True,
                        "owner": result["owner"],
                        "history": history
                    }
                else:
                    response = {"registered": False}

                sock.sendto(json.dumps(response).encode(), addr)

            elif message["type"] == "new_block":
                print("Received a new block from another peer!")
                block_data = message["data"]
                new_block = Block(
                    block_data["index"],
                    block_data["prev_hash"],
                    block_data["transactions"],
                    block_data["nonce"],
                    block_data["hash"],
                    block_data["timestamp"]
                )

                # Check if block extends current chain
                if new_block.prev_hash == bc.chain[-1].hash:
                    if bc.is_valid_block(new_block):
                        bc.chain.append(new_block)
                        print("Block added to blockchain!")
                        broadcast_block(sock, new_block, peer_list)
                    else:
                        print("Malicious block detected & blocked!")
                else:
                    print(f"Received block that doesn't match current chain. Current hash: {bc.chain[-1].hash}, Block prev_hash: {new_block.prev_hash}")
                    # Add block to potential forks
                    if bc.add_fork(new_block):
                        # Check if we need to request missing blocks
                        missing_blocks = bc.get_missing_blocks(new_block.hash)
                        if missing_blocks:
                            print(f"Requesting missing blocks: {missing_blocks}")
                            # Request blocks from all peers
                            for peer_ip, peer_port in peer_list:
                                request_blocks(sock, missing_blocks[0], (peer_ip, peer_port))
                                # Also request the block itself in case we're missing it
                                request_blocks(sock, new_block.hash, (peer_ip, peer_port))
                                
                                # Also request the entire blockchain
                                print(f"Requesting full blockchain from {peer_ip}:{peer_port}")
                                message = {
                                    "type": "get_blockchain"
                                }
                                sock.sendto(json.dumps(message).encode(), (peer_ip, peer_port))
                                
                        # Try to resolve forks
                        if bc.resolve_forks():
                            print("Resolved fork by switching to longer chain")
                            # Broadcast the new chain to peers
                            for block in bc.chain:
                                broadcast_block(sock, block, peer_list)
                    else:
                        print("Failed to add block to forks")
                        # Still try to request the block in case we need it
                        for peer_ip, peer_port in peer_list:
                            request_blocks(sock, new_block.hash, (peer_ip, peer_port))

            elif message["type"] == "request_blocks":
                print(f"Received request for blocks starting with hash {message['data']['start_hash']}")
                start_hash = message["data"]["start_hash"]
                blocks = []
                current_hash = start_hash

                # Find blocks in our chain that match the requested hash
                for block in reversed(bc.chain):
                    if block.hash == current_hash:
                        print(f"Found block {block.hash} in main chain")
                        blocks.append(block.__dict__)
                        current_hash = block.prev_hash
                    else:
                        break

                # Also check fork chains
                for fork_chain in bc.forks.values():
                    for block in reversed(fork_chain):
                        if block.hash == current_hash:
                            print(f"Found block {block.hash} in fork chain")
                            blocks.append(block.__dict__)
                            current_hash = block.prev_hash
                            break

                if blocks:
                    print(f"Sending {len(blocks)} blocks in response")
                    response = {
                        "type": "blocks",
                        "data": blocks
                    }
                    sock.sendto(json.dumps(response).encode(), addr)
                else:
                    print("No matching blocks found")

            elif message["type"] == "blocks":
                print(f"Received {len(message['data'])} blocks for fork chain")
                # Process received blocks
                blocks = []
                for block_data in message["data"]:
                    block = Block(
                        block_data["index"],
                        block_data["prev_hash"],
                        block_data["transactions"],
                        block_data["nonce"],
                        block_data["hash"],
                        block_data["timestamp"]
                    )
                    blocks.append(block)
                    
                # Try to add blocks to forks
                for block in reversed(blocks):  # Process from oldest to newest
                    if bc.add_fork(block):
                        print(f"Added block {block.hash} to fork chain")
                    else:
                        print(f"Failed to add block {block.hash} to fork chain")
                        
                # Try to resolve forks
                if bc.resolve_forks():
                    print("Resolved fork by switching to longer chain")
                    # Broadcast the new chain to peers
                    for block in bc.chain:
                        broadcast_block(sock, block, peer_list)
                else:
                    print("No fork resolution needed")

            elif message["type"] == "get_blockchain":
                print("Received request for blockchain data")
                # Convert blocks to dict format for JSON serialization
                chain_data = [block.__dict__ for block in bc.chain]
                response = {
                    "status": "success",
                    "chain": chain_data
                }
                sock.sendto(json.dumps(response).encode(), addr)
                
                # Broadcast all our blocks as well
                print("Broadcasting all blocks in response to get_blockchain")
                for block in bc.chain:
                    broadcast_block(sock, block, [addr])

            else:
                print(f"Unknown message type: {message['type']}")

        except Exception as e:
            print(f"Error processing message: {e}")
            continue


def request_blocks(sock, start_hash, addr):
    """Request previous blocks from a peer to build a fork chain"""
    message = {
        "type": "request_blocks",
        "data": {
            "start_hash": start_hash
        }
    }
    try:
        print(f"Sending block request for hash {start_hash} to {addr}")
        sock.sendto(json.dumps(message).encode(), addr)
    except Exception as e:
        print(f"Error requesting blocks from {addr}: {e}")


def broadcast_block(sock, block, peer_list):
    """Broadcast a block to all peers"""
    message = {
        "type": "new_block",
        "data": block.__dict__
    }
    encoded_message = json.dumps(message).encode()

    for peer_ip, peer_port in peer_list:
        try:
            print(f"Broadcasting block {block.hash} to {peer_ip}:{peer_port}")
            sock.sendto(encoded_message, (peer_ip, peer_port))
        except Exception as e:
            print(f"Error broadcasting to {peer_ip}:{peer_port}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python node.py [port]")
        sys.exit(1)
    
    my_port = int(sys.argv[1])
    start_node(my_port)





# import socket
# import sys
# import json

# Take port number from command line
'''my_port = int(sys.argv[1])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", my_port))

print(f"Node listening on port {my_port}...")

while True:
    data, addr = sock.recvfrom(4096)
    message = json.loads(data.decode())
    print(f"Received from {addr}: {message}")'''


'''elif message["type"] == "transfer":
                print("Received a transfer request!")
                tx = {
                    "type": "transfer",
                    "serial_number": message["data"]["serial_number"],
                    "from": message["data"]["from"],
                    "to": message["data"]["to"]

                }
                bc.add_block([tx])
                print(f"Transferred product: {tx}")'''
