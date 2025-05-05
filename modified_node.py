import socket
import sys
import json
from blockchain import Blockchain
from block import Block
from hashlib import sha256
import time

def start_malicious_node(my_port):
    """Starts running the malicious node over the UDP connection"""
    peer_list = [
        ("127.0.0.1", 5001),
        ("127.0.0.1", 5002),
        ("127.0.0.1", 5003),
    ]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", my_port))
    print(f"Malicious node running on port {my_port}...")

    bc = Blockchain()

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            message = json.loads(data.decode())
            print(f"Parsed JSON message: {message}")

            if message["type"] == "register":
                print("Maliciously handling register request!")

                serial = message["data"]["serial_number"]
                model = message["data"]["model"]
                brand = message["data"]["brand"]

                tx = {
                    "type": "register",
                    "serial_number": serial,
                    "model": model,
                    "owner": brand
                }

                # Build a block with an INVALID nonce and hash
                last_block = bc.chain[-1]
                index = last_block.index + 1
                prev_hash = last_block.hash
                transactions = [tx]

                fake_block = Block(index, prev_hash, transactions)
                fake_block.nonce = 0  # invalid nonce
                fake_block.hash = sha256("malicious".encode()).hexdigest()  # invalid hash

                print(f"Broadcasting malicious block with hash {fake_block.hash}")
                broadcast_block(sock, fake_block, peer_list)

                response = {"status": "malicious"}
                sock.sendto(json.dumps(response).encode(), addr)

            else:
                print(f"Ignoring message of type: {message['type']}")

        except Exception as e:
            print(f"Failed to parse or handle message: {e}")


def broadcast_block(sock, block, peer_list):
    """Broadcasts the malicious block to its peers, attempts to add to chain"""
    message = {
        "type": "new_block",
        "data": block.__dict__
    }
    encoded_message = json.dumps(message).encode()

    for peer_ip, peer_port in peer_list:
        sock.sendto(encoded_message, (peer_ip, peer_port))
        print(f"Sent malicious block to {peer_ip}:{peer_port}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python modified_node.py [port]")
        sys.exit(1)

    my_port = int(sys.argv[1])
    start_malicious_node(my_port)
