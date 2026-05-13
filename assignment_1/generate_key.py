from ipv8.keyvault.crypto import default_eccrypto

key = default_eccrypto.generate_key("curve25519")

# Save private key
with open("my_key.pem", "wb") as f:
    f.write(default_eccrypto.key_to_bin(key))