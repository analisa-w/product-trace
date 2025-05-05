from flask import Flask, request, render_template, redirect
import socket
import json
from datetime import datetime

app = Flask(__name__)

# Where your main node is running
NODE_IP = "127.0.0.1"
NODE_PORT = 5001

'''def send_udp_message(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(message).encode(), (NODE_IP, NODE_PORT))'''
def send_udp_message(message, port=NODE_PORT):
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)  # 2 second timeout
    sock.sendto(json.dumps(message).encode(), (NODE_IP, port))

    try:
        data, _ = sock.recvfrom(4096)
        ack = json.loads(data.decode())
        return ack
    except socket.timeout:
        return {"status": "timeout"}


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        serial = request.form["serial_number"]
        model = request.form["model"]
        brand = request.form["brand"]
        node_port = int(request.form["node_port"])

        message = {
            "type": "register",
            "data": {
                "serial_number": serial,
                "model": model,
                "brand": brand
            }
        }
        ack = send_udp_message(message, port=node_port)

        if ack.get("status") == "accepted":
            return render_template("register_success.html", serial=serial, model=model, brand=brand)
        else:
            reason = ack.get("reason", "Potentially malicious block detected during registration.")
            return render_template("register_fail.html", serial=serial, reason=reason)

    return render_template("register.html")

@app.route('/transfer', methods=["GET", "POST"])
def transfer():
    if request.method == "POST":
        serial = request.form["serial_number"]
        from_owner = request.form["from_owner"]
        to_owner = request.form["to_owner"]

        message = {
            "type": "transfer",
            "data": {
                "serial_number": serial,
                "from": from_owner,
                "to": to_owner
            }
        }
        ack = send_udp_message(message)

        if ack["status"] == "accepted":
            return render_template("transfer_success.html", serial=serial, from_owner=from_owner, to_owner=to_owner)
        elif ack["status"] == "rejected":
            return render_template("transfer_fail.html", serial=serial, reason=ack.get("reason", "Unknown reason"))
        else:
            return render_template("transfer_fail.html", serial=serial, reason="No response from node (timeout).")
    return render_template("transfer.html")


@app.route('/verify', methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        serial = request.form["serial_number"]

        message = {
            "type": "verify",
            "data": {
                "serial_number": serial
            }
        }
        ack = send_udp_message(message)

        if ack.get("registered"):
            return render_template("verify_success.html", serial=serial, owner=ack["owner"], history=ack["history"])
        else:
            return render_template("verify_fail.html", serial=serial)

    return render_template("verify.html")

@app.route('/blockchain')
def blockchain():
    message = {
        "type": "get_blockchain",
        "data": {}
    }
    ack = send_udp_message(message)
    
    if ack.get("status") == "success":
        print("BLOCKCHAIN DATA:", ack)
        return render_template("blockchain.html", chain=ack["chain"])
    else:
        return render_template("blockchain_error.html")

@app.template_filter('datetime')
def datetime_filter(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    app.run(debug=True)
