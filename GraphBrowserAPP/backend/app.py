from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from collections import deque

from  .. import graph as g

app = Flask(__name__)
CORS(app)

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOCAL_DB_PATH = os.path.join(BASE_DIR, "local_database.db")
API_DB_PATH = os.path.join(BASE_DIR, "api_database.db")

ALLOWED_LANGUAGES = {"EN", "ES"}
ALLOWED_MODES = {"words", "all"}
ALLOWED_SOURCES = {"local", "api"}


def get_db(source):
    if source == "local":
        return get_local_db()
    elif source == "api":
        return get_api_db()
    else:
        raise ValueError("Invalid database source. Use 'local' or 'api'.")

def get_local_db():

    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_api_db():

    conn = sqlite3.connect(API_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/api/search")
def search():
    word = request.args.get("word", "").strip().lower()
    hops = int(request.args.get("hops", 2))
    language = request.args.get("language", "EN").strip().upper()
    mode = request.args.get("mode", "words").strip().lower()
    source = request.args.get("source", "local").strip().lower()
    
    if not word:
        return jsonify({"error": "No word provided"}), 400

    if language is None or language not in ALLOWED_LANGUAGES:
        language = None

    if mode not in ALLOWED_MODES:
        return jsonify({"error": "Invalid mode"}), 400
    
    if source not in ALLOWED_SOURCES:
        return jsonify({"error": "Invalid source"}), 400

    nodes, edges, adjacency = g.build_graph(conn=get_db(source=source), language=language, mode=mode)

    
    seeds = []
    for nid, node in nodes.items():
        label = node["label"].lower()
        if node["type"] == "hub" and label == word:
            seeds.append(nid)
        elif node["type"] == "concept" and label.startswith(word+"_"):
            seeds.append(nid)

    if not seeds:
        for nid, node in nodes.items():
            if word == node["label"].lower():
                seeds.append(nid)

    if not seeds:
        return jsonify({"nodes": [], "edges": [], "message": f"No nodes found for '{word}'"}), 200

    visited = set(seeds)
    queue = deque((s, 0) for s in seeds)
    while queue:
        current, depth = queue.popleft()
        if depth >= hops:
            continue
        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, depth + 1))

    subgraph_nodes = [nodes[nid] for nid in visited if nid in nodes]
    subgraph_edges = [
        e for e in edges
        if e["source"] in visited and e["target"] in visited
    ]

    # sacar duplicadas
    seen_edges = set()
    unique_edges = []
    for e in subgraph_edges:
        key = (e["source"], e["target"], e["relation"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)

    return jsonify({
        "nodes": subgraph_nodes,
        "edges": unique_edges,
        "seeds": seeds,
        "total_nodes": len(subgraph_nodes),
        "total_edges": len(unique_edges),
    })


@app.route("/api/words")
def list_words():
    # para autocompletar palabraas al escribir
    # sacar esta parte??
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT word FROM words ORDER BY word;")
    words = [row["word"] for row in cursor.fetchall()]
    conn.close()
    return jsonify(words)


@app.route("/api/stats")
def stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM words")
    word_count = cursor.fetchone()["c"]
    cursor.execute("SELECT COUNT(*) as c FROM relations")
    rel_count = cursor.fetchone()["c"]
    conn.close()
    return jsonify({"words": word_count, "relations": rel_count})


app.run(debug=True, port=5000)

