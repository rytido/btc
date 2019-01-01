import json
import numpy as np
import networkx as nx

data = json.load(open('lightning_graph.json'))
pubkey = open("pubkey.txt").read().strip()

def get_nodes(data):
    nodes = {}
    for d in data:
        w = d[2]["weight"] / 1000
        nodes[d[0]] = nodes.get(d[0], 0) + w
        nodes[d[1]] = nodes.get(d[1], 0) + w
    return nodes

nodes = get_nodes(data)
print("node count: {}".format(len(nodes)))

def compute_score(paths, nodes):
    hop_data = []
    for id, path in paths.items():
        if len(path) > 1:
            hops = len(path) - 1
            capacity = nodes[id]
            hop_data.append(np.log(capacity) / hops)
    return sum(hop_data) / len(hop_data)

def make_graph(id=None):
    graph = nx.Graph()
    graph.add_edges_from(data)
    if id is not None:
        graph.add_edges_from([(pubkey, id, {"weight":1000})])
    paths = nx.shortest_path(graph, source=pubkey)
    score = compute_score(paths, nodes)
    hop_distribution = np.bincount([len(p)-1 for p in paths.values()])
    return score, hop_distribution



current_score, hop_distribution = make_graph()
print(current_score, hop_distribution)

onions = json.load(open("onions.json"))

#for id in nodes.keys():
for id in onions:
    new_score, hop_distribution = make_graph(id)
    if new_score > current_score:
        print(new_score, hop_distribution, id)
        current_score = new_score
