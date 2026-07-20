from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import sqlite3
from pyvis.network import Network

app = Flask(__name__)
CORS(app)

conn = sqlite3.connect("local_database.db", check_same_thread=False)
cursor = conn.cursor()

colors = {
    "ES": "#4CAF50",
    "EN": "#D31111",
}

def make_graph(word):
    net = Network(
        height="800px",
        width="100%",
        directed=True,
        notebook=False
    )

    cursor.execute("""
    SELECT
        CONCAT(w1.word, '_', w1.concept) AS source,
        CONCAT(w2.word, '_', w2.concept) AS target,
        r.relation_type, w1.language, w2.language,
        w1.word AS source_word, w2.word AS target_word
    FROM relations r
    JOIN words w1 ON r.word1_id = w1.id
    JOIN words w2 ON r.word2_id = w2.id
    WHERE w1.word = ? OR w2.word = ?
    """, (word, word))
    rows = cursor.fetchall()
    print(f"Retrieved {len(rows)} rows for word '{word}'")

    nodes = set()
    hub_nodes = set()

    def add_hub(word, lang):
        hub_id = f"__hub__{word}"
        if hub_id not in hub_nodes:
            net.add_node(hub_id, label=word, color=colors[lang], size=30, shape="ellipse")
            hub_nodes.add(hub_id)
        return hub_id

    for source, target, relation, source_lang, target_lang, source_word, target_word in rows:
        if "negocio_bn:00014137n" in (source, target):
            continue
        if source.endswith("_"):
            source = source[:-1]
        if target.endswith("_"):
            target = target[:-1]

        if source not in nodes:
            net.add_node(source, label=source, color=colors[source_lang])
            nodes.add(source)
        if target not in nodes:
            net.add_node(target, label=target, color=colors[target_lang])
            nodes.add(target)

        if relation == "translation":
            net.add_edge(source, target, label=relation, title=relation,
                         arrows="to, from", color="#000000")
        else:
            net.add_edge(source, target)

        src_hub = add_hub(source_word, source_lang)
        tgt_hub = add_hub(target_word, target_lang)
        if (source, src_hub) not in nodes:
            net.add_edge(source, src_hub, color="#aaaaaa", width=0.5)
            nodes.add((source, src_hub))
        if (target, tgt_hub) not in nodes:
            net.add_edge(target, tgt_hub, color="#aaaaaa", width=0.5)
            nodes.add((target, tgt_hub))

    net.write_html("word.html")


@app.route("/graph", methods=["GET"])
def graph():
    word = request.args.get("word", "").strip()
    if not word:
        return jsonify({"error": "No word provided"}), 400
    try:
        make_graph(word)
        return send_file("word.html")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return send_file("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)