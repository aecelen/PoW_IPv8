import hashlib
import struct
from dotenv import load_dotenv
import os

load_dotenv()

email = os.getenv("EMAIL")
github_url = os.getenv("GITHUB_URL")

def compute_hash(email, github_url):
    prefix = email.encode("utf-8") + b"\n" + github_url.encode("utf-8") + b"\n"
    nonce = 0
    while True:
        nonce_bytes = struct.pack(">q", nonce)
        hash_value = hashlib.sha256(prefix + nonce_bytes).digest()
        if hash_value[0] == 0 and hash_value[1] == 0 and hash_value[2] == 0 and hash_value[3] < 16:
            print(f"Found nonce: {nonce}")
            print(f"Hash: {hash_value.hex()}")
            with open("nonce.txt", "w") as f:
                f.write(str(nonce))
            return nonce
        nonce += 1

compute_hash(email, github_url)