from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256
from base64 import b64decode
from Crypto.Util.Padding import unpad
import random


def generate_secret_word(length):
    """
    returns a randomly generated secret word
    """

    vowels = 'aeiou'
    consonants = 'bcdfghjklmnpqrstvwxyz'
    secret_word = ''

    for i in range(length):
        if i % 2 == 0:
            secret_word += random.choice(consonants)
        else:
            secret_word += random.choice(vowels)

    return secret_word


def load_private_key():
    try:
        with open('portal/security/privatekey.pem', 'r') as file:
            key_contents = file.read()
            private_key = RSA.import_key(key_contents)
            return private_key
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail="Private key file not found!")
    except ValueError as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading private key: {e}")


def decrypt_key(encrypted_key):
    try:
        private_key = load_private_key()
        cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
        decrypted_key_bytes = cipher.decrypt(b64decode(encrypted_key))
        decrypted_key_str = decrypted_key_bytes.decode()
        return decrypted_key_str
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error decrypting key: {e}")


def decrypt_message(data: str, key: str, passedIv: str):
    try:
        secret_key = key
        iv = passedIv
        ciphertext = b64decode(data)
        derived_key = b64decode(secret_key)
        cipher = AES.new(derived_key, AES.MODE_CBC, iv.encode('utf-8'))
        decrypted_data = cipher.decrypt(ciphertext)
        unpad_data = unpad(decrypted_data, 16).decode("utf-8")
        return unpad_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error decrypting message: {e}")
