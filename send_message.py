import socket
import json
import sys

def send_message(dest_ip, dest_port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(message).encode(), (dest_ip, dest_port))
    print(f"Sent message to {dest_ip}:{dest_port}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python send_message.py [dest_ip] [dest_port]")
        sys.exit(1)

    dest_ip = sys.argv[1]
    dest_port = int(sys.argv[2])

    fake_register = {
        "type": "register",
        "data": {
            "serial_number": "GUCCI456",
            "model": "Marmont Flap",
            "brand": "Gucci"
        }
    } 

    '''fake_transfer = {
        "type": "transfer",
        "data": {
            "serial_number": "GUCCI456",
            "from": "Gucci",
            "to": "Analisa"
        }
    }'''

    send_message(dest_ip, dest_port, fake_register)
    # send_message(dest_ip, dest_port, fake_transfer)

