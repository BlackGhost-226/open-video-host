from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa



def write_private_key(private_key_path: str, private_key: rsa.RSAPrivateKey):
    with open(private_key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))

def read_private_key(private_key_path: str):
    with open(private_key_path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def private_key_object_to_string(private_key: rsa.RSAPrivateKey):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")



def write_public_key(public_key_path: str, public_key: rsa.RSAPublicKey):
    with open(public_key_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def read_public_key(public_key_path: str):
    with open(public_key_path, "rb") as f:
        return serialization.load_pem_public_key(f.read())

def public_key_object_to_string(public_key: rsa.RSAPublicKey):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
