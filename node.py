import binascii

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from collections import OrderedDict

import block
import wallet
import transaction
import time
import requests
import uuid


class Node:
    def __init__(self, bootstrap_address=None, clients=None, node_address=None, is_bootstrap=None):
        self.myWallet = self.create_wallet()
        self.myBlock = None
        self.chain = []
        self.NBC = None
        self.current_id = None
        self.ring = []
        self.unspent_transactions = []
        self.ip_address = node_address

        if not is_bootstrap:
            self.contact_bootstrap(bootstrap_address, node_address)
        else:
            self.current_id = 0
            self.nodes = clients
            self.create_genesis_block(clients)
            self.register_node_to_ring(self.myWallet.public_key, bootstrap_address, 0, self.unspent_transactions)
            self.NBC = clients * 100

    def contact_bootstrap(self, bootstrap_address, node_address):
        r = requests.post(bootstrap_address + '/bootstrap/register',
                          data={'public_key': self.myWallet.public_key, 'ip_address': node_address})
        data = r.json()
        self.current_id = data['id']
        if data['last_node']:
            r = requests.get(bootstrap_address + '/get/ring')
            data = r.json()
            self.ring = data['ring']
            self.chain = data['chain']
            self.create_new_block(self.chain[-1]['hash'])
            print('got my ring')
            r = requests.get(bootstrap_address + '/get/first_transactions')
            data = r.json()
            print('transaction done! Time to validate it ...')
            self.validate_transaction(data)

    def create_genesis_block(self, clients):
        first_transaction = transaction.Transaction(0, 0, self.myWallet.public_key, clients * 100, None, 0, 0)
        first_unspent_transaction = {
            'id': uuid.uuid4().int,
            'transaction_id': 0,
            'recipient': self.myWallet.public_key,
            'value': clients * 100
        }
        self.unspent_transactions.append(first_unspent_transaction)
        genesis_block = block.Block(0, time.time(), first_transaction.to_dict(), 1)
        self.chain.append(genesis_block.to_dict())
        self.create_new_block(self.chain[-1]['hash'])

    def create_new_block(self, prev_hash):
        self.myBlock = block.Block(None, time.time(), [], prev_hash)

    def create_wallet(self):
        return wallet.Wallet()

    def get_balance(self):
        self.NBC = self.myWallet.get_balance(self.unspent_transactions)
        print(self.NBC)

    def register_node_to_ring(self, public_key, ip_address, node_id, balance):
        node = {
            'public_key': public_key,
            'ip_address': ip_address,
            'node_id': node_id,
            'balance': balance
        }
        self.ring.append(node)
        last_node = False
        if len(self.ring) == self.nodes:
            last_node = True
        return last_node

    def create_transaction(self, receiver, value):
        my_transaction = transaction.Transaction(self.myWallet.public_key, self.myWallet.private_key, receiver, value)
        self.broadcast_transaction(my_transaction)
        return my_transaction

    def broadcast_transaction(self, my_transaction):
        for t in self.ring:
            # r = requests.post(bootstrap_address + '/bootstrap/register', data={
            #     'public_key': self.myWallet.public_key,
            #     'ip_address': node_address
            # })
            self.NBC = 1  # this is temp line of code until the requests are complete

    def validate_transaction(self, v_transaction):
        print('The validation begins')
        signature_verification = self.verify_signature(v_transaction)
        if signature_verification:
            print('signature is valid!')
            if all(x in self.ring[v_transaction['transaction']['sender_id']]['balance'] for x in v_transaction['transaction']['transaction_inputs']):
                print('transaction is valid!')
                for t in v_transaction['transaction']['transaction_inputs']:
                    self.ring[v_transaction['transaction']['sender_id']]['balance'].remove(t)
                self.add_transaction_to_block(v_transaction)
                self.ring[v_transaction['transaction']['sender_id']]['balance']\
                    .append(v_transaction['transaction']['transaction_outputs'][0])
                self.ring[v_transaction['transaction']['recipient_id']]['balance']\
                    .append(v_transaction['transaction']['transaction_outputs'][1])

    def verify_signature(self, v_transaction):
        """
        Check that the provided signature corresponds to transaction
        signed by the public key (sender_address)
        """
        print("Let's check the signature")
        public_key = RSA.importKey(binascii.unhexlify(v_transaction['transaction']['sender_address']))
        verifier = PKCS1_v1_5.new(public_key)
        check = OrderedDict({'sender_address': v_transaction['transaction']['sender_address'],
                             'recipient_address': v_transaction['transaction']['recipient_address'],
                             'value': v_transaction['transaction']['value']})
        h = SHA.new(str(check).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(v_transaction['transaction']['signature']))

    def add_transaction_to_block(self, v_transaction):
        print('Now going to add the transaction to myBlock')
        self.myBlock.transactions.append(v_transaction)
    # def mine_block(self):

    # def broadcast_block(self):

    # def valid_proof(self, difficulty=MINING_DIFFICULTY):

    # def valid_chain(self, chain):

    # def resolve_conflicts(self):
