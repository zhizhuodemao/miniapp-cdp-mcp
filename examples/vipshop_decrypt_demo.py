"""
VIP.com WeChat Mini Program (唯品会小程序) - mina_edata Encryption/Decryption Demo
Disclaimer: This script is for educational and security research purposes only.

This demonstrates how a complex multi-layer encryption payload discovered using
the miniapp-cdp MCP server can be reproduced in Python.

Algorithm:
1. Base Secret generation using 3DES (ECB mode) with zero-padded key.
2. Suffixing a dynamic session token (VIP_TANK) to the base secret.
3. AES Key derivation via MD5 digest.
4. Payload encryption using AES-CBC with a randomly generated 16-byte IV.
5. Base64 encoding the concatenated IV and Ciphertext.
"""

import base64
import urllib.parse
import hashlib
import os
from Crypto.Cipher import DES3, AES
from Crypto.Util.Padding import unpad, pad

def get_base_secret() -> str:
    """
    Extract the root secret by decrypting a hardcoded 3DES ciphertext.
    """
    key_3des = b"ed1d2af1b7a9bc"
    encrypted_secret_b64 = "8Cx7kryAR8lfsYcO53oqlH+5wx+A0H9WubKEx8neBZCK2L5r84f2aw=="
    
    # 3DES keys must be 16 or 24 bytes in pycryptodome. 
    # CryptoJS automatically pads insufficient keys with 0s.
    key_3des_padded = key_3des.ljust(24, b'\0')
    cipher_3des = DES3.new(key_3des_padded, DES3.MODE_ECB)
    
    encrypted_secret = base64.b64decode(encrypted_secret_b64)
    base_secret_padded = cipher_3des.decrypt(encrypted_secret)
    
    return unpad(base_secret_padded, 8).decode('utf-8')

def get_aes_key(base_secret: str, vip_tank: str = "") -> bytes:
    """
    Derive the final 16-byte AES key using MD5.
    """
    secret_str = base_secret
    if vip_tank:
        secret_str += "&" + vip_tank
        
    return hashlib.md5(secret_str.encode('utf-8')).digest()

def encrypt_mina_edata(payload_dict: dict, vip_tank: str = "") -> str:
    """
    Encrypt the payload dictionary into the mina_edata parameter.
    """
    # Create the querystring-like payload (without URL encoding)
    payload_str = "&".join(f"{k}={v}" for k, v in payload_dict.items())
    
    base_secret = get_base_secret()
    aes_key = get_aes_key(base_secret, vip_tank)
    
    # Generate 16 bytes random IV
    iv = os.urandom(16)
    
    # AES-CBC encryption
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
    ciphertext = cipher_aes.encrypt(pad(payload_str.encode('utf-8'), 16))
    
    # Concat IV + Ciphertext
    final_bytes = iv + ciphertext
    
    mina_edata = base64.b64encode(final_bytes).decode('utf-8')
    return urllib.parse.quote(mina_edata)

def decrypt_mina_edata(mina_edata_encoded: str, vip_tank: str = "") -> str:
    """
    Decrypt an intercepted mina_edata string back to readable parameters.
    """
    mina_edata = urllib.parse.unquote(mina_edata_encoded)
    edata_bytes = base64.b64decode(mina_edata)
    
    iv = edata_bytes[:16]
    ciphertext = edata_bytes[16:]
    
    base_secret = get_base_secret()
    aes_key = get_aes_key(base_secret, vip_tank)
    
    cipher_aes = AES.new(aes_key, AES.MODE_CBC, iv)
    plaintext_padded = cipher_aes.decrypt(ciphertext)
    
    return unpad(plaintext_padded, 16).decode('utf-8')

if __name__ == "__main__":
    # Example payload matching the app's structure
    sample_payload = {
        "app_name": "shop_weixin_mina",
        "client": "wechat_mini_program",
        "app_version": "4.0",
        "t": "1776707227"
    }
    
    print("--- VIP.com mini program encryption demo ---")
    print(f"Original Payload:\n{sample_payload}\n")
    
    encrypted = encrypt_mina_edata(sample_payload)
    print(f"Encrypted mina_edata:\n{encrypted}\n")
    
    decrypted = decrypt_mina_edata(encrypted)
    print(f"Decrypted Payload:\n{decrypted}")
