from flask import Flask, request, render_template, redirect
import socket
import json

app = Flask(__name__)

# Where your main node is running
NODE_IP = "127.0.0.1"
NODE_PORT = 5001

'''def send_udp_message(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(message).encode(), (NODE_IP, NODE_PORT))'''
def send_udp_message(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)  # 2 second timeout
    sock.sendto(json.dumps(message).encode(), (NODE_IP, NODE_PORT))

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

        message = {
            "type": "register",
            "data": {
                "serial_number": serial,
                "model": model,
                "brand": brand
            }
        }
        send_udp_message(message)
        return "Product Registered! ✅"

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
            return "Ownership Transferred! ✅"
        elif ack["status"] == "rejected":
            return f"Transfer Rejected ❌: {ack.get('reason', 'Unknown reason')}"
        else:
            return "No response from node (timeout). ❌"

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
            return render_template("verify_result.html", serial=serial, owner=ack["owner"], history=ack["history"])
        else:
            return f"Product {serial} is NOT registered. ❌"

    return render_template("verify.html")


if __name__ == "__main__":
    app.run(debug=True)
