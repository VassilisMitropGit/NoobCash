import binascii
import copy
import json
import hashlib
import threading
from pprint import pprint

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from collections import OrderedDict, deque

import block
import wallet
import transaction
import time
import requests
import uuid

CAPACITY = 6
MINING_DIFFICULTY = 2


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
        self.transaction_pool = deque()
        self.block_pool = deque()
        self.available_transactions = threading.Semaphore(value=0)
        self.available_blocks = threading.Semaphore(value=0)
        myThread = threading.Thread(target=self.thread_function)
        myThread.start()

        if not is_bootstrap:
            self.contact_bootstrap(bootstrap_address, node_address)
        else:
            self.current_id = 0
            self.nodes = clients
            self.create_genesis_block(clients)
            self.register_node_to_ring(self.myWallet.public_key, bootstrap_address, 0, copy.deepcopy(self.unspent_transactions))
            self.NBC = clients * 100

    def add_transaction_to_pool(self, t):
        self.transaction_pool.appendleft(t)
        self.available_transactions.release()

    def add_block_to_pool(self, b):
        self.block_pool.appendleft(b)
        self.available_blocks.release()

    def thread_function(self):
        while True:
            self.available_transactions.acquire()
            print('acquired')
            myTransaction = self.transaction_pool.pop()
            self.validate_transaction(myTransaction)
            if len(self.myBlock.transactions) == CAPACITY:
                print('WE HAVE TO MINE!')
                self.mine_block()
                if self.myBlock.nonce is not None:
                    self.myBlock.hash = self.myBlock.calculate_hash()
                    self.broadcast_block()
                self.myBlock = None
                self.create_new_block(self.chain[-1]['hash'])

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
            for i in range(0, len(self.ring) - 1):
                r = requests.get(bootstrap_address + '/get/first_transactions')
                data = r.json()
                print('transaction done! Time to validate it ...')
                self.validate_transaction(data)
            self.mine_block()
            self.myBlock.hash = self.myBlock.calculate_hash()
            self.chain.append(self.myBlock.to_dict())
            self.myBlock = None
            for node_ip in self.ring[:-1]:
                r = requests.post(node_ip['ip_address'] + '/post/starting_blockchain', json={'chain': self.chain})
            self.create_new_block(self.chain[-1]['hash'])
            pprint(self.ring)

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
        self.NBC = self.myWallet.get_balance(self.ring[self.current_id]['balance'])
        print(self.NBC)
        return self.NBC

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

    def mine_block(self):
        last_block = self.chain[-1]
        nonce = self.proof_of_work()
        last_hash = last_block['hash']
        print(nonce)
        self.myBlock.nonce = nonce

    def proof_of_work(self):
        last_block = self.chain[-1]
        last_hash = last_block['hash']

        nonce = 0
        while self.valid_proof(self.myBlock.transactions, last_hash, nonce) is False:
            lock = self.available_blocks.acquire(blocking=False)
            if lock:
                the_block = self.block_pool.pop()
                if self.valid_block(the_block):
                    self.chain.append(the_block)
                    return None
            nonce += 1

        return nonce

    def valid_proof(self, transactions, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        guess = (str(transactions)+str(last_hash)+str(nonce)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == '0'*difficulty

    def valid_block(self, b):
        last_block = self.chain[-1]
        last_hash = last_block['hash']
        if b['previous_hash'] == last_hash:
            block_string = json.dumps({
                "nonce": b['nonce'],
                "timestamp": b['timestamp'],
                "transactions": b['transactions'],
                "previous_hash": b['previous_hash']
            }, sort_keys=True).encode()
            my_hash = hashlib.sha256(block_string).hexdigest()
            if my_hash == b['hash']:
                return True
            else:
                return False

    def broadcast_block(self):
        for b in self.ring:
            if b['node_id'] != self.current_id:
                r = requests.post(b['ip_address'] + '/broadcast/block',
                                  json={'block': copy.deepcopy(self.myBlock.to_dict())})

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            # Delete the reward transaction
            transactions = block['transactions'][:-1]
            # Need to make sure that the dictionary is ordered. Otherwise we'll get a different hash
            transaction_elements = ['sender_address', 'recipient_address', 'value']
            transactions = [OrderedDict((k, transaction[k]) for k in transaction_elements) for transaction in
                            transactions]

            if not self.valid_proof(transactions, block['previous_hash'], block['nonce'], MINING_DIFFICULTY):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            print('http://' + node + '/chain')
            response = requests.get('http://' + node + '/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def view_transactions(self):
        last_block = self.chain[-1]
        return last_block['transactions']
