import os
import json
import requests
import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import grpc
import codecs

def slacker(channel, text):
    webhook_url = os.environ['SLACK']
    slack_data = {"channel": channel, "text": text}
    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    return response.text

def show_dict(data):
    return "\n".join("%s: %s" % (k, v) for k,v in sorted(data.items()))

def save_dict(data, filename):
    json.dump(data, open(filename, 'w'))

def load_dict(filename):
    if os.path.exists(filename):
        return json.load(open(filename))
    else:
        return {}

# Due to updated ECDSA generated tls.cert we need to let gprc know that
# we need to use that cipher suite otherwise there will be a handhsake
# error when we communicate with the lnd rpc server.
os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

cert = open(os.path.expanduser('~/.lnd/tls.cert'), 'rb').read()

def metadata_callback(context, callback):
    with open(os.path.expanduser('~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon'), 'rb') as f:
        macaroon_bytes = f.read()
        macaroon = codecs.encode(macaroon_bytes, 'hex')
        callback([('macaroon', macaroon)], None)

# build ssl credentials using the cert the same as before
cert_creds = grpc.ssl_channel_credentials(cert)
# now build meta data credentials
auth_creds = grpc.metadata_call_credentials(metadata_callback)
# combine the cert credentials and the macaroon auth credentials
# such that every call is properly encrypted and authenticated
combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)
# finally pass in the combined credentials when creating a channel
channel = grpc.secure_channel('localhost:10009', combined_creds)
stub = lnrpc.LightningStub(channel)

# now every call will be made with the macaroon already included
peer_info = stub.ListPeers(ln.ListPeersRequest())
peers = [p.pub_key for p in peer_info.peers]

channel_info = stub.ListChannels(ln.ListChannelsRequest()).channels
channel_peers = set([c.remote_pubkey for c in channel_info])

non_channel_peers = [p for p in peers if p not in channel_peers]
if len(non_channel_peers)>7:
    peer = non_channel_peers[0]
    stub.DisconnectPeer(ln.DisconnectPeerRequest(pub_key=peer))

data = {}

data['total_satoshis_sent'] = sum([c.total_satoshis_sent for c in channel_info])
data['total_satoshis_received'] = sum([c.total_satoshis_received for c in channel_info])
data['num_inactive_channels'] = sum([1 for c in channel_info if c.active == False])

info = stub.GetInfo(ln.GetInfoRequest())
data['num_active_channels'] = info.num_active_channels

filename = os.path.expanduser('~/btc/lnd.json')
saved_data = load_dict(filename)

if data != saved_data:
    save_dict(data, filename)
    data['num_peers'] = info.num_peers
    network_info = stub.GetNetworkInfo(ln.NetworkInfoRequest())
    data['total_num_nodes'] = network_info.num_nodes
    data['total_num_channels'] = network_info.num_channels
    slacker('#lnd', show_dict(data))
