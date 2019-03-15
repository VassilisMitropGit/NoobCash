import block
import wallet
import transaction
import time
import requests


class Node:
    def __init__(self, bootstrap_address=None, clients=None, node_address=None, is_bootstrap=None):
        self.myWallet = self.create_wallet()
        self.myBlock = None
        self.chain = None
        self.NBC = None
        self.current_id = None
        self.ring = []

        if not is_bootstrap:
            self.contact_bootstrap(bootstrap_address)
        else:
            self.current_id = 0
            self.NBC = clients * 100

    def contact_bootstrap(self, bootstrap_address):
       # r = requests.post(bootstrap_address + '/bootstrap/register', data={'public_key': self.myWallet.public_key})
        self.NBC = 1

    def create_new_block(self, prev_hash):
        self.myBlock = block.Block(None, time.time(), None, prev_hash)

    def create_wallet(self):
        return wallet.Wallet

    def register_node_to_ring(self, public_key, ip_address, node_id, balance):
        node = {
            'public_key': public_key,
            'ip_address': ip_address,
            'node_id': node_id,
            'balance': balance
        }
        self.ring.append(node)

    # add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
    # bootstrap node informs all other nodes and gives the request node an id and 100 NBCs

    def create_transaction(self, receiver, signature, value):
        transaction.Transaction(self.myWallet.public_key, self.myWallet.private_key, receiver, value)
    # remember to broadcast it

    # def broadcast_transaction(self):

    # def validate_transaction(self):

    # use of signature and NBCs balance

    # def add_transaction_to_block(self):

    # if enough transactions  mine

    # def mine_block(self):

    # def broadcast_block(self):

    # def valid_proof(self, difficulty=MINING_DIFFICULTY):

    # concencus functions

    # def valid_chain(self, chain):

    # check for the longer chain accroose all nodes

    # def resolve_conflicts(self):
# resolve correct chain



