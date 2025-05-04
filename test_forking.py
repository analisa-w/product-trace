import socket
import json
import time
import threading
import signal
import sys
import os
import subprocess
import psutil
from node import start_node
from modified_node import start_malicious_node

# Global list to track active threads and their sockets
active_threads = []
active_sockets = []
node_processes = []

def find_process_using_port(port):
    """Find the process ID using the specified port"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.net_connections():
                if conn.laddr.port == port:
                    return proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def kill_process_on_port(port):
    """Kill any process using the specified port"""
    pid = find_process_using_port(port)
    if pid:
        try:
            process = psutil.Process(pid)
            process.terminate()  # Try graceful termination first
            time.sleep(0.5)
            if process.is_running():
                process.kill()  # Force kill if still running
            time.sleep(0.5)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def cleanup_ports():
    """Clean up ports by binding and closing sockets"""
    ports = [5001, 5002, 5003]
    
    # First, try to kill any processes using these ports
    for port in ports:
        kill_process_on_port(port)
    
    # Then try to close any existing sockets
    for sock in active_sockets:
        try:
            sock.close()
        except:
            pass
    active_sockets.clear()
    
    # Then try to bind and close new sockets
    for port in ports:
        try:
            # Try TCP socket first
            for _ in range(3):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind(("127.0.0.1", port))
                    sock.close()
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Warning: Could not bind TCP port {port} (attempt {_+1}): {e}")
                    time.sleep(0.2)
            
            # Then try UDP socket
            for _ in range(3):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind(("127.0.0.1", port))
                    sock.close()
                    time.sleep(0.2)
                except Exception as e:
                    print(f"Warning: Could not bind UDP port {port} (attempt {_+1}): {e}")
                    time.sleep(0.2)
                    
        except Exception as e:
            print(f"Error cleaning up port {port}: {e}")
        finally:
            time.sleep(0.5)

def start_node_in_thread(port, is_malicious=False):
    """Start a node in a separate thread"""
    if is_malicious:
        thread = threading.Thread(target=start_malicious_node, args=(port,))
    else:
        thread = threading.Thread(target=start_node, args=(port,))
    thread.daemon = True
    thread.start()
    active_threads.append(thread)
    return thread

def cleanup_threads():
    """Clean up all active threads"""
    for thread in active_threads:
        if thread.is_alive():
            # Try to join with timeout
            thread.join(timeout=1.0)
            if thread.is_alive():
                # If thread is still alive, try to terminate it
                print(f"Warning: Thread {thread.name} did not terminate gracefully")
                # Try to kill the process
                for port in [5001, 5002, 5003]:
                    kill_process_on_port(port)
    active_threads.clear()
    
    # Additional cleanup
    cleanup_ports()
    time.sleep(2)  # Give more time for cleanup to complete

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nCleaning up and exiting...")
    cleanup_threads()
    sys.exit(0)

# Register signal handler for graceful exit
signal.signal(signal.SIGINT, signal_handler)

def send_register_request(port, serial, model, brand):
    """Send a register request to a node"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = {
        "type": "register",
        "data": {
            "serial_number": serial,
            "model": model,
            "brand": brand
        }
    }
    sock.sendto(json.dumps(message).encode(), ("127.0.0.1", port))
    data, _ = sock.recvfrom(4096)
    return json.loads(data.decode())

def verify_product(port, serial):
    """Verify a product's status"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = {
        "type": "verify",
        "data": {
            "serial_number": serial
        }
    }
    sock.sendto(json.dumps(message).encode(), ("127.0.0.1", port))
    data, _ = sock.recvfrom(4096)
    return json.loads(data.decode())

def test_natural_fork():
    print("\n=== Testing Natural Fork ===")
    cleanup_threads()  # Clean up any existing threads
    time.sleep(2)  # Wait for cleanup to complete
    
    try:
        # Start three normal nodes
        node1_thread = start_node_in_thread(5001)
        time.sleep(2)  # Increased delay for node startup
        node2_thread = start_node_in_thread(5002)
        time.sleep(2)  # Increased delay for node startup
        node3_thread = start_node_in_thread(5003)
        time.sleep(3)  # Increased delay for node startup

        # Register different products on different nodes
        serial1 = "TEST123"
        serial2 = "TEST456"
        model = "Test Model"
        brand = "Test Brand"

        # Register product 1 on node 1
        result1 = send_register_request(5001, serial1, model, brand)
        print(f"Node 1 registration: {result1}")
        time.sleep(2)  # Wait for block propagation

        # Register product 2 on node 2
        result2 = send_register_request(5002, serial2, model, brand)
        print(f"Node 2 registration: {result2}")
        time.sleep(2)  # Wait for block propagation

        # Wait for fork resolution
        time.sleep(15)  # Increased wait time for fork resolution

        # Verify products on all nodes
        print("\nNode 5001 verifications:")
        verify1 = verify_product(5001, serial1)
        verify2 = verify_product(5001, serial2)
        print(f"Product 1: {verify1}")
        print(f"Product 2: {verify2}")

        print("\nNode 5002 verifications:")
        verify1 = verify_product(5002, serial1)
        verify2 = verify_product(5002, serial2)
        print(f"Product 1: {verify1}")
        print(f"Product 2: {verify2}")

        print("\nNode 5003 verifications:")
        verify1 = verify_product(5003, serial1)
        verify2 = verify_product(5003, serial2)
        print(f"Product 1: {verify1}")
        print(f"Product 2: {verify2}")

        # Check if all nodes have the same chain length
        chain_lengths = []
        for port in [5001, 5002, 5003]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = {"type": "get_blockchain"}
            sock.sendto(json.dumps(message).encode(), ("127.0.0.1", port))
            data, _ = sock.recvfrom(4096)
            response = json.loads(data.decode())
            chain_lengths.append(len(response["chain"]))
            sock.close()

        print(f"\nChain lengths: {chain_lengths}")
        if len(set(chain_lengths)) == 1:
            print("✅ All nodes have the same chain length")
        else:
            print("❌ Chain lengths differ between nodes")

    finally:
        # Clean up
        cleanup_threads()
        time.sleep(2)

def test_malicious_fork():
    print("\n=== Testing Malicious Fork ===")
    cleanup_threads()  # Clean up any existing threads
    time.sleep(2)  # Wait for cleanup to complete
    
    try:
        # Start one normal and two malicious nodes
        node1_thread = start_node_in_thread(5001)
        time.sleep(1)
        node2_thread = start_node_in_thread(5002, is_malicious=True)
        time.sleep(1)
        node3_thread = start_node_in_thread(5003, is_malicious=True)
        time.sleep(2)

        # Register products on different nodes
        serial1 = "MALICIOUS1"
        serial2 = "MALICIOUS2"
        model = "Malicious Model"
        brand = "Malicious Brand"

        # Register on normal node
        result1 = send_register_request(5001, serial1, model, brand)
        print(f"Normal node registration: {result1}")

        # Register on malicious nodes
        result2 = send_register_request(5002, serial2, model, brand)
        print(f"Malicious node 1 registration: {result2}")
        result3 = send_register_request(5003, serial2, model, brand)
        print(f"Malicious node 2 registration: {result3}")

        # Wait for fork resolution
        time.sleep(10)  # Increased wait time for fork resolution

        # Verify products on all nodes
        print("\nNode 5001 verifications:")
        verify1 = verify_product(5001, serial1)
        verify2 = verify_product(5001, serial2)
        print(f"Product 1: {verify1}")
        print(f"Product 2: {verify2}")

        print("\nNode 5002 verifications:")
        verify1 = verify_product(5002, serial1)
        verify2 = verify_product(5002, serial2)
        print(f"Product 1: {verify1}")
        print(f"Product 2: {verify2}")

        print("\nNode 5003 verifications:")
        verify1 = verify_product(5003, serial1)
        verify2 = verify_product(5003, serial2)
        print(f"Product 1: {verify1}")
        print(f"Product 2: {verify2}")

        # Check chain lengths
        chain_lengths = []
        for port in [5001, 5002, 5003]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = {"type": "get_blockchain"}
            sock.sendto(json.dumps(message).encode(), ("127.0.0.1", port))
            data, _ = sock.recvfrom(4096)
            response = json.loads(data.decode())
            chain_lengths.append(len(response["chain"]))
            sock.close()

        print(f"\nChain lengths: {chain_lengths}")
        if len(set(chain_lengths)) == 1:
            print("✅ All nodes have the same chain length")
        else:
            print("❌ Chain lengths differ between nodes")

    finally:
        # Clean up
        cleanup_threads()
        time.sleep(2)

def test_network_partition():
    print("\n=== Testing Network Partition ===")
    cleanup_threads()  # Clean up any existing threads
    time.sleep(2)  # Wait for cleanup to complete
    
    try:
        # Start three nodes
        node1_thread = start_node_in_thread(5001)
        time.sleep(1)
        node2_thread = start_node_in_thread(5002)
        time.sleep(1)
        node3_thread = start_node_in_thread(5003)
        time.sleep(2)

        # Create a network partition by removing node2 from node1's peer list
        # This simulates a network failure between node1 and node2
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = {
            "type": "remove_peer",
            "data": {
                "port": 5002
            }
        }
        sock.sendto(json.dumps(message).encode(), ("127.0.0.1", 5001))
        sock.close()

        # Register products on different partitions
        serial1 = "PARTITION1"
        serial2 = "PARTITION2"
        model = "Partition Model"
        brand = "Partition Brand"

        # Register on partition 1 (node1)
        result1 = send_register_request(5001, serial1, model, brand)
        print(f"Partition 1 registration: {result1}")

        # Register on partition 2 (node2 and node3)
        result2 = send_register_request(5002, serial2, model, brand)
        print(f"Partition 2 registration (node2): {result2}")
        result3 = send_register_request(5003, serial2, model, brand)
        print(f"Partition 2 registration (node3): {result3}")

        # Wait for network to stabilize
        time.sleep(10)  # Increased wait time for network stabilization

        # Verify products on all nodes
        print("\nNode 5001 verifications:")
        verify1 = verify_product(5001, serial1)
        verify2 = verify_product(5001, serial2)
        print(f"Product 1: {verify1}")
        print(f"Product 2: {verify2}")

        print("\nNode 5002 verifications:")
        verify1 = verify_product(5002, serial1)
        verify2 = verify_product(5002, serial2)
        print(f"Product 1: {verify1}")
        print(f"Product 2: {verify2}")

        print("\nNode 5003 verifications:")
        verify1 = verify_product(5003, serial1)
        verify2 = verify_product(5003, serial2)
        print(f"Product 1: {verify1}")
        print(f"Product 2: {verify2}")

        # Check chain lengths
        chain_lengths = []
        for port in [5001, 5002, 5003]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = {"type": "get_blockchain"}
            sock.sendto(json.dumps(message).encode(), ("127.0.0.1", port))
            data, _ = sock.recvfrom(4096)
            response = json.loads(data.decode())
            chain_lengths.append(len(response["chain"]))
            sock.close()

        print(f"\nChain lengths: {chain_lengths}")
        if len(set(chain_lengths)) == 1:
            print("✅ All nodes have the same chain length")
        else:
            print("❌ Chain lengths differ between nodes")

    finally:
        # Clean up
        cleanup_threads()
        time.sleep(2)

if __name__ == "__main__":
    print("Starting fork testing...")
    
    # Run tests one at a time
    print("\nWhich test would you like to run?")
    print("1. Natural Fork Test")
    print("2. Malicious Fork Test")
    print("3. Network Partition Test")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            test_natural_fork()
        elif choice == "2":
            test_malicious_fork()
        elif choice == "3":
            test_network_partition()
        elif choice == "4":
            print("Exiting...")
            cleanup_threads()
            break
        else:
            print("Invalid choice. Please try again.")
        
        # Wait for user to press Enter before continuing
        input("\nPress Enter to continue...") 