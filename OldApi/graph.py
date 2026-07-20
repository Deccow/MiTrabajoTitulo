import networkx as nx
import sqlite3

# Create (or connect to) a local database file
conn = sqlite3.connect("local_database.db")

# Create a cursor to execute SQL commands
cursor = conn.cursor()

def analyze_graph(net, name="graph"):
    # Convert pyvis → networkx
    G = nx.DiGraph()
    for node in net.nodes:
        G.add_node(node["id"])
    for edge in net.edges:
        G.add_edge(edge["from"], edge["to"])

    total = G.number_of_nodes()

    # --- 1. Nodes connected to only one other node ---
    # In a directed graph, use total degree (in + out)
    degree_one = [n for n, d in G.degree() if d == 1]
    pct_degree_one = len(degree_one) / total * 100
    print(f"Nodes with only 1 connection: {len(degree_one)} ({pct_degree_one:.1f}%)")

    # Show up to 10 examples
    sample = degree_one[:10]
    print(f"  Sample (up to 10): {sample}")

    # --- 2. Average degree ---
    avg_degree = sum(d for _, d in G.degree()) / total
    density = nx.density(G)
    print(f"Average degree: {avg_degree:.2f}")

    with open("graph_stats.txt", "w") as f:
        f.write(f"Nodes with only 1 connection: {len(degree_one)} ({pct_degree_one:.1f}%)\n")
        f.write(f"Average degree: {avg_degree:.2f}\n")

import pyvis
from pyvis.network import Network

def make_graph(name="graph"):
    
    net = Network(
        height="800px",
        width="100%",
        directed=True,
        notebook=False
    )

    
    colors = {
        "ES": "#4CAF50",
        "EN": "#D31111",
    }


    cursor.execute("""
    SELECT
        CONCAT(w1.word, '_', w1.concept) AS source,
        CONCAT(w2.word, '_', w2.concept) AS target,
        r.relation_type, w1.language, w2.language,
        w1.word AS source_word, w2.word AS target_word, 
        w1.concept AS source_concept, w2.concept AS target_concept
    FROM relations r
    JOIN words w1 ON r.word1_id = w1.id
    JOIN words w2 ON r.word2_id = w2.id;
    """)
    rows = cursor.fetchall()

    nodes = set()
    hub_nodes = set()  # track which word hubs already exist

    def add_hub(word, lang):
        """Add a hub node for a bare word if not already present."""
        hub_id = f"__hub__{word}"
        if hub_id not in hub_nodes:
            net.add_node(
                hub_id,
                label=word,
                color=colors[lang],
                size=30,        # make hub visually bigger
                shape="ellipse" # or "star", "diamond", etc.
            )
            hub_nodes.add(hub_id)
        return hub_id

    for source, target, relation, source_lang, target_lang, source_word, target_word, source_concept, target_concept in rows:
        if source.endswith("_"):
            source = source[:-1]
        if target.endswith("_"):
            target = target[:-1]

        # Add concept nodes
        if source not in nodes:
            net.add_node(source, label=source, color=colors[source_lang])
            nodes.add(source)
        if target not in nodes:
            net.add_node(target, label=target, color=colors[target_lang])
            nodes.add(target)

        # Add edges between concepts
        if relation == "translation":
            net.add_edge(source, target, label=relation, title=relation,
                         arrows="to, from", color="#000000")
        else:
            net.add_edge(source, target)

        # Connect each concept node to its word hub
        if source_concept != None:
            src_hub = add_hub(source_word, source_lang)
            if (source, src_hub) not in nodes:
                net.add_edge(source, src_hub, color="#aaaaaa", width=0.5)
                nodes.add((source, src_hub))  # prevent duplicate hub edges

        if target_concept != None:
            tgt_hub = add_hub(target_word, target_lang)
            if (target, tgt_hub) not in nodes:
                net.add_edge(target, tgt_hub, color="#aaaaaa", width=0.5)
                nodes.add((target, tgt_hub))

    analyze_graph(net, name)
    net.write_html(f"{name}.html")