import os, json, pickle, random, networkx as nx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.join(BASE_DIR, "city")
GRAPH_PATH = os.path.join(CITY_DIR, "moscow_graph.pkl")
HOTSPOTS_PATH = os.path.join(CITY_DIR, "hotspots.json")

class CityRouter:
    def __init__(self):
        with open(GRAPH_PATH, "rb") as f:
            self.G = pickle.load(f)
        with open(HOTSPOTS_PATH, "r") as f:
            self.hotspots = json.load(f)
        self.nodes = list(self.G.nodes)
        self.hotspot_nodes = [{"node": self._nearest_node(h["lat"], h["lon"]),
                               "weight": h["weight"], "name": h["name"]} for h in self.hotspots]

    def _nearest_node(self, lat, lon):
        return min(self.nodes, key=lambda n: (self.G.nodes[n]["y"] - lat)**2 + (self.G.nodes[n]["x"] - lon)**2)

    def random_node(self):
        return random.choice(self.nodes)

    def weighted_hotspot_node(self):
        return random.choices(self.hotspot_nodes, weights=[h["weight"] for h in self.hotspot_nodes], k=1)[0]["node"]

    def shortest_path(self, src, dst):
        try:
            return nx.shortest_path(self.G, src, dst, weight="length")
        except nx.NetworkXNoPath:
            return [src]

    def node_coords(self, node):
        n = self.G.nodes[node]
        return n["y"], n["x"]
