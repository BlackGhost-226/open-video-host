from fastapi import FastAPI
from cryptography.hazmat.primitives.asymmetric import rsa
from os.path import exists
from os import getenv

from .utils import write_private_key
from .utils import write_public_key
from .utils import read_private_key
from .utils import read_public_key
from .utils import public_key_object_to_string
from .utils import private_key_object_to_string

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

from bcrypt import gensalt

app = FastAPI()

keys_path = "/auth_authority/rsa/"
private_key_path = keys_path+"private_key.pem"
public_key_path = keys_path+"public_key.pem"

if not exists(private_key_path):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    write_private_key(private_key_path=private_key_path, private_key=private_key)
    write_public_key(public_key_path=public_key_path, public_key=public_key)
elif not exists(public_key_path) and exists(private_key_path):
    private_key = read_private_key(private_key_path=private_key_path)
    public_key = private_key.public_key()
    write_public_key(public_key_path=public_key_path, public_key=public_key)

private_key = read_private_key(private_key_path=private_key_path)
public_key = read_public_key(public_key_path=public_key_path)

private_key_pem = private_key_object_to_string(private_key=private_key)
public_key_pem = public_key_object_to_string(public_key=public_key)

engine = create_engine(getenv("DATABASE_URI"))
Session = sessionmaker(engine)
#Base.metadata.drop_all(engine)
#Base.metadata.create_all(engine)

bcrypt_salt = gensalt()

from . import routes
