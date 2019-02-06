import os
import codecs
import rpc_pb2 as ln
import rpc_pb2_grpc as lnrpc
import grpc


# Due to updated ECDSA generated tls.cert we need to let gprc know that
# we need to use that cipher suite otherwise there will be a handhsake
# error when we communicate with the lnd rpc server.
os.environ["GRPC_SSL_CIPHER_SUITES"] = "HIGH+ECDSA"


def metadata_callback(context, callback):
    macaroon_path = os.path.expanduser("~/.lnd/data/chain/bitcoin/mainnet/invoice.macaroon")
    with open(macaroon_path, "rb") as f:
        macaroon_bytes = f.read()
        macaroon = codecs.encode(macaroon_bytes, "hex")
        callback([("macaroon", macaroon)], None)


def open_channel():
    """open a grpc channel:
    build ssl credentials using cert
    build meta data credentials
    combine the cert credentials and the macaroon auth credentials
    finally pass in the combined credentials when creating a channel
    """
    cert = open(os.path.expanduser("~/.lnd/tls.cert"), "rb").read()
    cert_creds = grpc.ssl_channel_credentials(cert)
    auth_creds = grpc.metadata_call_credentials(metadata_callback)
    combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)
    channel = grpc.secure_channel("localhost:10009", combined_creds)
    return channel


channel = open_channel()
stub = lnrpc.LightningStub(channel)

invoice_request = ln.Invoice(value=10000, expiry=7200)
invoice_response = stub.AddInvoice(invoice_request)
payment_request = invoice_response.payment_request
print(payment_request)

"""
lnbc100u1pw95fnupp5s9dvrxp4hh3nsxscaq8afdezzlzhf3ar7cegvurqvkjyau2fsw3sdqqcqzysxqr8pqyj52cwuwhwcf7d2rekgax2j8ysxwhaklw94yfhv9agjr9ye4kkgzy435vc2a84ufld7qurc37ghsh8gddrphjrfd35xyy678ft0x4tqqcvffcz
"""
