import os
import json

import codecs
import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import grpc
import pandas as pd

MESSAGE_SIZE_MB = 50 * 1024 * 1024

os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

def metadata_callback(context, callback):
    with open(os.path.expanduser('~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon'), 'rb') as f:
        macaroon_bytes = f.read()
        macaroon = codecs.encode(macaroon_bytes, 'hex')
        callback([('macaroon', macaroon)], None)

def get_creds():
    cert = open(os.path.expanduser('~/.lnd/tls.cert'), 'rb').read()
    # build ssl credentials using the cert the same as before
    cert_creds = grpc.ssl_channel_credentials(cert)
    # now build meta data credentials
    auth_creds = grpc.metadata_call_credentials(metadata_callback)
    # combine the cert credentials and the macaroon auth credentials
    combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)
    return combined_creds

channel_options = [
    ('grpc.max_message_length', MESSAGE_SIZE_MB),
    ('grpc.max_receive_message_length', MESSAGE_SIZE_MB)
]

channel = grpc.secure_channel('localhost:10009', get_creds(), channel_options)
stub = lnrpc.LightningStub(channel)

identity_pubkey = stub.GetInfo(ln.GetInfoRequest()).identity_pubkey
#print(identity_pubkey)

lgraph = stub.DescribeGraph(ln.ChannelGraphRequest())
edges = lgraph.edges
#nodes = lgraph.nodes

data = [(e.node1_pub, e.node2_pub, {"weight": e.capacity}) for e in edges]

json.dump(data, open("lightning_graph.json", 'w'))