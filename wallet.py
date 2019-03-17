import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4


class Wallet:

    def __init__(self):
        random_gen = Crypto.Random.new().read
        private_key = RSA.generate(1024, random_gen)
        public_key = private_key.publickey()
        self.public_key = binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
        self.private_key = binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii')
        self.balance = 0

    def public_key(self):
        return self.public_key

    def private_key(self):
        return self.private_key

    def get_balance(self, unspent_transactions):
        self.balance = 0
        for t in unspent_transactions:
            self.balance += t[1]

        return self.balance
