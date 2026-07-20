import networkx as nx

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


def build_graph(conn, language=None, word=None, mode="words"):
    """
    Build and return a NetworkX Graph.

    Node attributes:
        label
        lang
        type

    Edge attributes:
        relation
    """

    rows = fetch_edges(conn, language=language, word=word, mode=mode)

    G = nx.Graph()

    def add_node(nid, label, lang, ntype):
        if not G.has_node(nid):
            G.add_node(
                nid,
                label=label,
                lang=lang,
                type=ntype,
            )

    for row in rows:



        relation = row["relation_type"]

        src_lang = row["source_lang"]
        tgt_lang = row["target_lang"]

        if mode in ("all", "no_hubs"):

            src = clean_id(row["source"])
            tgt = clean_id(row["target"])

            src_concept = row["source_concept"]
            tgt_concept = row["target_concept"]

            src_word = row["source_word"]
            tgt_word = row["target_word"]

            add_node(src, src, src_lang, "concept")
            add_node(tgt, tgt, tgt_lang, "concept")

        else:

            src = clean_id(row["source"])+row["source_lang"]
            tgt = clean_id(row["target"])+row["target_lang"]

            src_concept = None
            tgt_concept = None

            src_word = row["source"]
            tgt_word = row["target"]

            add_node(src, src_word, src_lang, "word")
            add_node(tgt, tgt_word, tgt_lang, "word")

        G.add_edge(
            src,
            tgt,
            relation=relation,
        )

        if mode == "all":

            if src_concept:

                hub = f"__hub__{src_word}"

                add_node(
                    hub,
                    src_word,
                    src_lang,
                    "hub",
                )

                G.add_edge(
                    src,
                    hub,
                    relation="hub",
                )

            if tgt_concept:

                hub = f"__hub__{tgt_word}"

                add_node(
                    hub,
                    tgt_word,
                    tgt_lang,
                    "hub",
                )

                G.add_edge(
                    tgt,
                    hub,
                    relation="hub",
                )
    G.remove_edges_from(nx.selfloop_edges(G))
    return G


def build_full_graph(conn):
    return build_graph(conn)