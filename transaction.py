import hashlib
import json
import uuid
from collections import OrderedDict

import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import requests
from flask import Flask, jsonify, request, render_template


class Transaction:

    def __init__(self, sender_address, sender_private_key, recipient_address, value, transaction_inputs, sender_id, recipient_id):
        self.sender_address = sender_address
        self.sender_private_key = sender_private_key
        self.recipient_address = recipient_address
        self.value = value
        self.transaction_inputs = transaction_inputs
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        if sender_private_key is not 0:
            self.signature = self.sign_transaction()
            self.transaction_id = self.calculate_hash()
            self.transaction_outputs = self.create_outputs()

    def to_dict(self):
        return OrderedDict({'sender_address': self.sender_address,
                            'recipient_address': self.recipient_address,
                            'value': self.value})

    def sign_transaction(self):
        """
        Sign transaction with private key
        """
        private_key = RSA.importKey(binascii.unhexlify(self.sender_private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(self.to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')

    def create_outputs(self):
        balance = 0
        for t_input in self.transaction_inputs:
            balance = balance + t_input['value']
        first_output = {
            'id': uuid.uuid4().int,
            'transaction_id': self.transaction_id,
            'recipient': self.sender_address,
            'value': balance - self.value
        }
        second_output = {
            'id': uuid.uuid4().int,
            'transaction_id': self.transaction_id,
            'recipient': self.recipient_address,
            'value': self.value
        }
        outputs = [first_output, second_output]
        return outputs

    def calculate_hash(self):
        transaction_string = json.dumps({
            "sender_address": self.sender_address,
            "recipient_address": self.recipient_address,
            "value": self.value,
            "transaction_inputs": self.transaction_inputs,
            "signature": self.signature
        }, sort_keys=True).encode()
        return hashlib.sha256(transaction_string).hexdigest()

    def to_dict_transaction(self):
        return OrderedDict({'sender_address': self.sender_address,
                            'recipient_address': self.recipient_address,
                            'value': self.value,
                            'transaction_id': self.transaction_id,
                            'signature': self.signature,
                            'transaction_outputs': self.transaction_outputs,
                            'transaction_inputs': self.transaction_inputs,
                            'sender_id': self.sender_id,
                            'recipient_id': self.recipient_id})
