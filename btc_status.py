import os
import json
import requests
from collections import Counter
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

def slacker(channel, text):
    webhook_url = os.environ['SLACK']
    slack_data = {"channel": channel, "text": text}
    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    return response.text

cnxn_str = "http://{}:{}@{}".format(os.environ['RPC_USER'], os.environ['RPC_PASSWORD'], os.environ['NODE_IP'])
def engine(commands):
    return AuthServiceProxy(cnxn_str).batch_(commands)

def shift_fee(fee):
    return round(float(fee * 100000), 1)

def get_tx(txid):
    return engine([["getrawtransaction", txid, True]])[0]

def much_info():
	commands = [["getpeerinfo"], ["getblockcount"], ["getmempoolinfo"], ["getbestblockhash"],
					["estimatesmartfee", 1, "ECONOMICAL"], ["estimatesmartfee", 6, "ECONOMICAL"], ["estimatesmartfee", 72, "ECONOMICAL"]]
	names = ["_".join(str(s) for s in c) for c in commands]
	results = engine(commands)
	kv = dict(zip(names, results))
	block = engine([["getblock", kv["getbestblockhash"]]])[0]
	peers = kv["getpeerinfo"]

	cleaned = {
	"peers":len(peers),
	"blocks":kv["getblockcount"], #['blocks']
	"block_tx":len(block['tx']),
	"block_mb":round(block['size']/1000000, 4),
	#"difficulty":round(float(kv["getblockchaininfo"]['difficulty']/1000000000000), 3),
	"memsize_tx":kv["getmempoolinfo"]['size'],
	"memsize_mb":round(kv["getmempoolinfo"]['bytes']/1000000, 2),
	"feerate_01block":shift_fee(kv["estimatesmartfee_1_ECONOMICAL"]['feerate']),
	"feerate_01hour":shift_fee(kv["estimatesmartfee_6_ECONOMICAL"]['feerate']),
	"feerate_12hour":shift_fee(kv["estimatesmartfee_72_ECONOMICAL"]['feerate']),
	}

	peer_versions = Counter(['peer_' + p['subver'][1:].split(':')[0].lower() for p in peers])
	ban_scores = Counter(['score_' + str(p['banscore']) for p in peers])

	cleaned = {**cleaned, **peer_versions, **ban_scores}
	return cleaned


infostr = "\n".join("%s: %s" % (k, v) for k,v in sorted(much_info().items()))

slacker('#alerts', infostr)

"""
blocktx = engine([["getblock", kv["getbestblockhash"], 2]])[0]['tx']
outs = [t['vout'] for t in blocktx[1:]]
max_tx_out = round(max([max([o['value'] for o in out]) for out in outs]),2)
"""

