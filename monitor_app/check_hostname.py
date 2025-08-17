""" This script retrieves the current machine's hostname and generates a secure API key."""
import socket
import secrets

# Get current machine's hostname
hostname = socket.gethostname()
print("Hostname:", hostname)

secure_key = secrets.token_hex(32)  # 64 hex chars (256 bits)
print("Secure API Key:", secure_key)
