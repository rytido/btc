import os
import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import grpc
import codecs
import pandas as pd

pd.options.display.max_colwidth = 255
os.environ["GRPC_SSL_CIPHER_SUITES"] = "HIGH+ECDSA"


def metadata_callback(context, callback):
    mac_file = "~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon"
    with open(os.path.expanduser(mac_file), "rb") as f:
        macaroon_bytes = f.read()
        macaroon = codecs.encode(macaroon_bytes, "hex")
        callback([("macaroon", macaroon)], None)


cert = open(os.path.expanduser("~/.lnd/tls.cert"), "rb").read()
cert_creds = grpc.ssl_channel_credentials(cert)
auth_creds = grpc.metadata_call_credentials(metadata_callback)
combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)
channel = grpc.secure_channel("localhost:10009", combined_creds)
stub = lnrpc.LightningStub(channel)

channel_info = stub.ListChannels(ln.ListChannelsRequest()).channels

fields = [
    "remote_pubkey",
    "chan_id",
    "active",
    "capacity",
    "local_balance",
    "remote_balance",
    "csv_delay",
    "private",
]
chan_data = [[getattr(c, f) for f in fields] for c in channel_info]
df_chan = pd.DataFrame(chan_data, columns=fields).set_index("chan_id")
print(df_chan.sort_values(["active", "capacity", "private"], ascending=False))
print("\ncapital: {}".format(df_chan.local_balance.sum()))
