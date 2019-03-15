import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS


import block
import blockchain
import transaction
import node
import wallet

nodeid = 0
curr_node = None

app = Flask(__name__)

CORS(app)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/bootstrap/register', methods=['POST'])
def register_node():
    global nodeid
    nodeid += 1
    print(request.form['public_key'])
    response = {'id': nodeid}
    curr_node.register_node_to_ring()
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-b', '--bootstrap', default=False, type=bool, help='boolean to check if this node is the bootstrap node')
    parser.add_argument('-ba', '--baddress', default='http://localhost:5000', type=str, help='the ip address of the bootstrap node')
    parser.add_argument('-a', '--address', default='localhost:5000', type=str, help='the ip address of the current node')
    parser.add_argument('-c', '--clients', default=0, type=int, help='number of clients in the system')

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
