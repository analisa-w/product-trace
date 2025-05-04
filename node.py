import socket
import sys
import json
from blockchain import Blockchain
from block import Block


def start_node(my_port):

    peer_list = [
    ("127.0.0.1", 5002),  # Example: another node running on your computer
    ("127.0.0.1", 5003),    
    ]

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", my_port))
    print(f"Node is running and listening on port {my_port}...")

    bc = Blockchain()

    while True:
        data, addr = sock.recvfrom(4096)
        try:
            message = json.loads(data.decode())
            print(f"Parsed JSON message: {message}")

            if message["type"] == "register":
                print("Received a register request!")
                serial = message["data"]["serial_number"]
                result = bc.verify_product(serial)
                response = {}

                if result["registered"]:
                    print(f"Registration rejected, product {serial} already exists")
                    response = {
                            "status": "rejected", 
                            "reason": "Product with that serial number already exists."}
                    sock.sendto(json.dumps(response).encode(), addr)
                else:
                    tx = {
                        "type": "register",
                        "serial_number": message["data"]["serial_number"],
                        "model": message["data"]["model"],
                        "owner": message["data"]["brand"]  # Brand = initial owner
                    }
                    bc.add_block([tx])
                    print(f"Registered product: {tx}")
                    broadcast_block(sock, bc.chain[-1], peer_list)
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
                    bc.add_block([tx])
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

                incoming_block_data = message["data"]

                # Rebuild the Block object
                incoming_block = Block(
                    index=incoming_block_data["index"],
                    prev_hash=incoming_block_data["prev_hash"],
                    transactions=incoming_block_data["transactions"]
                )
                incoming_block.timestamp = incoming_block_data["timestamp"]
                incoming_block.nonce = incoming_block_data["nonce"]
                incoming_block.hash = incoming_block_data["hash"]

                # Verify and add to blockchain
                if incoming_block.prev_hash == bc.chain[-1].hash:
                    bc.chain.append(incoming_block)
                    print("Block added to blockchain!")
                else:
                    print("Block rejected — hash mismatch.")

            else:
                print(f"Unknown message type: {message['type']}")


        except Exception as e:
            print(f"Failed to parse JSON: {e}")


   
    '''while True:
        data, addr = sock.recvfrom(4096)
        try:
            message = json.loads(data.decode())
            print(f"Parsed JSON message: {message}")

            if message["type"] == "register":
                print("Received a register request!")
                # TODO: add this to blockchain
            elif message["type"] == "transfer":
                print("Received a transfer request!")
                # TODO: add this to blockchain
            else:
                print(f"Unknown message type: {message['type']}")

        except Exception as e:
            print(f"Failed to parse JSON: {e}")'''
def broadcast_block(sock, block, peer_list):
    message = {
        "type": "new_block",
        "data": block.__dict__
    }
    encoded_message = json.dumps(message).encode()

    for peer_ip, peer_port in peer_list:
        sock.sendto(encoded_message, (peer_ip, peer_port))
        print(f"Broadcasted new block to {peer_ip}:{peer_port}")




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
