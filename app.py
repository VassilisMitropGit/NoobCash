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


@app.route('/get/ring', methods=['GET'])
def get_ring():
    global curr_node
    response = {'ring': curr_node.ring}
    for node_ip in curr_node.ring[1:-1]:
        r = requests.post(node_ip['ip_address'] + '/post/ring', data={'ring': curr_node.ring})
        data = r.json()
        print(data['message'])
    return jsonify(response), 200


@app.route('/post/ring', methods=['POST'])
def post_ring():
    global curr_node
    curr_node.ring = request.form['ring']
    response = {'message': 'OK'}
    return jsonify(response), 200


@app.route('/bootstrap/register', methods=['POST'])
def register_node():
    global nodeid
    nodeid += 1
    last_node = curr_node.register_node_to_ring(request.form['public_key'], request.form['ip_address'], nodeid, 0)
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
    parser.add_argument('-c', '--clients', default=3, type=int, help='number of clients in the system')

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
