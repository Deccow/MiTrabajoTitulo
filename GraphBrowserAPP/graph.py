
def fetch_all_edges(conn):
    return fetch_edges(conn)


def fetch_edges(conn, language=None, word=None, mode="all"):
    if mode == "all":
        cursor = conn.cursor()
        cursor.execute("""
        SELECT
            w1.word || '_' || COALESCE(w1.concept, '') AS source,
            w2.word || '_' || COALESCE(w2.concept, '') AS target,
            r.relation_type,
            w1.language AS source_lang,
            w2.language AS target_lang,
            w1.word AS source_word,
            w2.word AS target_word,
            w1.concept AS source_concept,
            w2.concept AS target_concept
        FROM relations r
        JOIN words w1 ON r.word1_id = w1.id
        JOIN words w2 ON r.word2_id = w2.id
        WHERE (:lang IS NULL OR (w1.language = :lang AND w2.language = :lang))
        AND (:word IS NULL OR (w1.word = :word OR w2.word = :word))
        """, {"lang": language, "word": word})
        rows = cursor.fetchall()
        conn.close()
        return rows
    elif mode == "words":
        cursor = conn.cursor()
        cursor.execute("""
        SELECT DISTINCT 
        w1.word AS source, 
        w2.word AS target, 
        r.relation_type,
        w1.language AS source_lang,
        w2.language AS target_lang
        FROM relations r
        JOIN words w1 ON r.word1_id = w1.id
        JOIN words w2 ON r.word2_id = w2.id
        WHERE (:lang IS NULL OR (w1.language = :lang AND w2.language = :lang))
        AND (:word IS NULL OR (w1.word = :word OR w2.word = :word))
        """, {"lang": language, "word": word})
        rows = cursor.fetchall()
        conn.close()
        return rows


def clean_id(s):
    return s[:-1] if s.endswith("_") else s


def build_full_graph(conn):
    return build_graph(conn)

def build_graph(conn, language=None, word=None, mode="words"):
    """Builds a graph for the visualizer. Returns nodes, edges, and adjacency list."""
    rows = fetch_edges(conn, language=language, word=word, mode=mode)

    nodes = {}      # id -> {id, label, lang, type}
    edges = []      # {source, target, relation}
    adjacency = {}  # id -> set of neighbor ids

    def add_node(nid, label, lang, ntype="concept"):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": label, "lang": lang, "type": ntype}
        if nid not in adjacency:
            adjacency[nid] = set()

    for row in rows:
        src = clean_id(row["source"])
        tgt = clean_id(row["target"])
        relation = row["relation_type"]
        src_lang = row["source_lang"]
        tgt_lang = row["target_lang"]

        if mode in ["all", "no_hubs"]:
            src_concept = row["source_concept"]
            tgt_concept = row["target_concept"]
            add_node(src, src, src_lang, "concept")
            add_node(tgt, tgt, tgt_lang, "concept")
            src_word = row["source_word"]
            tgt_word = row["target_word"]
        else:
            src_word = row["source"]
            tgt_word = row["target"]
            add_node(src, src_word, src_lang, "concept")
            add_node(tgt, tgt_word, tgt_lang, "word")

        edges.append({"source": src, "target": tgt, "relation": relation})
        adjacency[src].add(tgt)
        adjacency[tgt].add(src)

        # Hub nodes
        if mode == "all":
            if src_concept:
                hub_id = f"__hub__{src_word}"
                add_node(hub_id, src_word, src_lang, "hub")
                edges.append({"source": src, "target": hub_id, "relation": "hub"})
                adjacency[src].add(hub_id)
                adjacency[hub_id].add(src)

            if tgt_concept:
                hub_id = f"__hub__{tgt_word}"
                add_node(hub_id, tgt_word, tgt_lang, "hub")
                edges.append({"source": tgt, "target": hub_id, "relation": "hub"})
                adjacency[tgt].add(hub_id)
                adjacency[hub_id].add(tgt)

    return nodes, edges, adjacency

