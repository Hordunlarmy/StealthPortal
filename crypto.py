from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode
import random


def generate_secret_word(length):
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
        with open('privatekey.pem', 'r') as file:
            key_contents = file.read()
            private_key = RSA.import_key(key_contents)
            return private_key
    except FileNotFoundError:
        print("Private key file not found!")
        return None
    except ValueError as e:
        print("Error loading private key:", e)
        return None


def decrypt_key(encrypted_key):
    try:
        private_key = load_private_key()
        if private_key is None:
            return None

        cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
        decrypted_key_bytes = cipher.decrypt(b64decode(encrypted_key))
        decrypted_key_str = decrypted_key_bytes.decode(
            'utf-8')
        return decrypted_key_str
    except Exception as e:
        print("Error decrypting key:", e)
        return None


def decrypt_message(data: str, key: str, passedIv: str) -> str:
    secret_key = key
    iv = passedIv
    ciphertext = b64decode(data)
    derived_key = b64decode(secret_key)
    cipher = AES.new(derived_key, AES.MODE_CBC, iv.encode('utf-8'))
    decrypted_data = cipher.decrypt(ciphertext)
    return unpad(decrypted_data, 16).decode("utf-8")
