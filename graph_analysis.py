import json
import networkx as nx

data = json.load(open('lightning_graph.json'))

graph = nx.Graph()
graph.add_edges_from(data)

pubkey = open("pubkey.txt").read().strip()
paths = nx.shortest_path(graph, source=pubkey, weight="weight")
print(next(iter(paths.items())))

nodes = {}
for d in data:
    w = d[2]["weight"]
    nodes[d[0]] = nodes.get(d[0], 0) + w
    nodes[d[1]] = nodes.get(d[1], 0) + w

print(len(nodes))
