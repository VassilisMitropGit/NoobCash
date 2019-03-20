import copy
from pprint import pprint

import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json

import block
import blockchain
import transaction
import node
import wallet

transaction_count = 1
nodeid = 0
curr_node = None
CAPACITY = 6
MINING_DIFFICULTY = 5

app = Flask(__name__)

CORS(app)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/post/starting_blockchain', methods=['POST'])
def get_starting_blockchain():
    global curr_node
    curr_node.myBlock = None
    curr_node.chain = request.get_json()['chain']
    pprint(curr_node.chain)
    response = {'message': 'OK'}
    return jsonify(response), 200


@app.route('/get/first_transactions', methods=['GET'])
def get_first_transactions():
    global curr_node
    global transaction_count
    t = transaction.Transaction(curr_node.myWallet.public_key, curr_node.myWallet.private_key, curr_node.ring[transaction_count]['public_key'], 100, copy.deepcopy(curr_node.ring[0]['balance']), 0, transaction_count)
    response = {'transaction': t.to_dict_transaction()}
    curr_node.validate_transaction({'transaction': t.to_dict_transaction()})
    for node_ip in curr_node.ring[1:-1]:
        r = requests.post(node_ip['ip_address'] + '/post/first_transactions', json={'transaction': t.to_dict_transaction()})
        data = r.json()
        print(data['message'])
    transaction_count += 1
    return jsonify(response), 200


@app.route('/post/first_transactions', methods=['POST'])
def post_first_transactions():
    global curr_node
    if len(curr_node.myBlock.transactions) < 6:
        transaction_data = request.get_json()['transaction']
        curr_node.validate_transaction({'transaction': transaction_data})
        response = {'message': 'OK'}
        return jsonify(response), 200


@app.route('/get/ring', methods=['GET'])
def get_ring():
    global curr_node
    response = {'ring': curr_node.ring, 'chain': curr_node.chain}
    for node_ip in curr_node.ring[1:-1]:
        r = requests.post(node_ip['ip_address'] + '/post/ring', json={'ring': curr_node.ring, 'chain': curr_node.chain})
        data = r.json()
        print(data['message'])
    return jsonify(response), 200


@app.route('/post/ring', methods=['POST'])
def post_ring():
    global curr_node
    curr_node.ring = request.get_json()['ring']
    curr_node.chain = request.get_json()['chain']
    curr_node.create_new_block(curr_node.chain[-1]['hash'])
    response = {'message': 'OK'}
    return jsonify(response), 200


@app.route('/bootstrap/register', methods=['POST'])
def register_node():
    global nodeid
    nodeid += 1
    last_node = curr_node.register_node_to_ring(request.form['public_key'], request.form['ip_address'], nodeid, [])
    response = {'id': nodeid, 'last_node': last_node}
    print(response)
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-b', '--bootstrap', default=True, action='store_false', help='boolean to check if this node is the bootstrap node')
    parser.add_argument('-ba', '--baddress', default='http://localhost:5000', type=str, help='the ip address of the bootstrap node')
    parser.add_argument('-a', '--address', default='localhost:5000', type=str, help='the ip address of the current node')
    parser.add_argument('-c', '--clients', default=4, type=int, help='number of clients in the system')

    args = parser.parse_args()
    port = args.port
    address = args.address
    bootstrap_address = args.baddress
    clients = args.clients
    bootstrap = args.bootstrap

    if bootstrap:
        curr_node = node.Node(bootstrap_address, clients, bootstrap_address, bootstrap)
    else:
        curr_node = node.Node(bootstrap_address, None, address, bootstrap)

    print("ZONK!")

    app.run(host='localhost', port=port)
