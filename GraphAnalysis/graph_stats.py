import os
import random
import statistics
import sys

import matplotlib.pyplot as plt
import networkx as nx
import GraphBrowserAPP.graph as g



def _avg_shortest_path_and_diameter(G, sample_size=200):
    nodes = list(G.nodes())
    if len(nodes) > sample_size:
        random.seed(0)
        sample = random.sample(nodes, sample_size)
    else:
        sample = nodes

    total_dist = 0
    total_pairs = 0
    diameter = 0
    diameter_path = []

    for src in sample:
        lengths = nx.single_source_shortest_path_length(G, src)
        dists = [(n, d) for n, d in lengths.items() if n != src]
        if dists:
            far_node, far_dist = max(dists, key=lambda x: x[1])
            total_dist += sum(d for _, d in dists)
            total_pairs += len(dists)
            if far_dist > diameter:
                diameter = far_dist
                diameter_path = nx.shortest_path(G, src, far_node)

    avg_path = total_dist / total_pairs if total_pairs else 0
    return avg_path, diameter, diameter_path


def local_clustering_coefficient(node_id, G):
    if G.degree(node_id) < 2:
        return 0.0
    return nx.clustering(G, node_id)


def _clustering_coefficient(G, node_ids, sample_size=500):
    nodes = list(node_ids)
    if len(nodes) > sample_size:
        random.seed(0)
        sample = random.sample(nodes, sample_size)
    else:
        sample = nodes

    eligible = [n for n in sample if G.degree(n) >= 2]
    if not eligible:
        return 0.0
    coeffs = nx.clustering(G, eligible)
    return statistics.mean(coeffs.values())


import statistics
import random
import networkx as nx
from networkx.algorithms.community import louvain_communities, modularity as nx_modularity


def _sampled_betweenness_centrality(G, k=100, seed=42):
    n = G.number_of_nodes()
    if n == 0:
        return {}
    k = min(k, n)
    return nx.betweenness_centrality(G, k=k, seed=seed, normalized=True)


def _sampled_closeness_centrality(G, k=100, seed=42):

    n = G.number_of_nodes()
    if n == 0:
        return {}
    k = min(k, n)
    rng = random.Random(seed)
    sample_nodes = rng.sample(list(G.nodes()), k)
    return {node: nx.closeness_centrality(G, u=node) for node in sample_nodes}


def graph_connectivity_stats(G, label="graph"):

    n = G.number_of_nodes()
    m = G.number_of_edges()

    degrees = dict(G.degree())
    deg_values = list(degrees.values())
    isolated = list(nx.isolates(G))

    top_n = 5
    top_degree_nodes = sorted(degrees.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    top_degree_info = [
        {"id": nid, "label": G.nodes[nid].get("label"), "type": G.nodes[nid].get("type"), "degree": d}
        for nid, d in top_degree_nodes
    ]

    components = sorted(nx.connected_components(G), key=len, reverse=True)
    giant_nodes = components[0] if components else set()
    giant = G.subgraph(giant_nodes)

    density = nx.density(G)

    avg_path, diameter, diameter_path_ids = (0, 0, [])
    if giant.number_of_nodes() > 1:
        avg_path, diameter, diameter_path_ids = _avg_shortest_path_and_diameter(giant)

    diameter_path_labels = [G.nodes[nid].get("label") for nid in diameter_path_ids]

    clustering = _clustering_coefficient(G, G.nodes())

    pagerank = nx.pagerank(G) if n else {}
    top_pagerank_nodes = sorted(pagerank.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    top_pagerank_info = [
        {"id": nid, "label": G.nodes[nid].get("label"), "type": G.nodes[nid].get("type"), "pagerank": round(score, 6)}
        for nid, score in top_pagerank_nodes
    ]

    communities = list(louvain_communities(G, seed=42)) if m > 0 else []
    community_sizes = sorted((len(c) for c in communities), reverse=True)
    louvain_modularity = round(nx_modularity(G, communities), 4) if communities else 0

    betweenness_k = min(100, n)
    betweenness = _sampled_betweenness_centrality(G, k=betweenness_k)
    top_betweenness_nodes = sorted(betweenness.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    top_betweenness_info = [
        {"id": nid, "label": G.nodes[nid].get("label"), "type": G.nodes[nid].get("type"), "betweenness": round(score, 6)}
        for nid, score in top_betweenness_nodes
    ]

    closeness_k = min(100, n)
    closeness = _sampled_closeness_centrality(G, k=closeness_k)
    top_closeness_nodes = sorted(closeness.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    top_closeness_info = [
        {"id": nid, "label": G.nodes[nid].get("label"), "type": G.nodes[nid].get("type"), "closeness": round(score, 6)}
        for nid, score in top_closeness_nodes
    ]


    try:
        degree_assortativity = nx.degree_assortativity_coefficient(G)
        if degree_assortativity is not None and not (isinstance(degree_assortativity, float) and degree_assortativity != degree_assortativity):
            degree_assortativity = round(degree_assortativity, 4)
        else:
            degree_assortativity = None
    except (nx.NetworkXError, ZeroDivisionError):
        degree_assortativity = None

    return {
        "label": label,
        "nodes": n,
        "edges": m,
        "density": round(density, 6),
        "avg_degree": round(statistics.mean(deg_values), 3) if deg_values else 0,
        "median_degree": statistics.median(deg_values) if deg_values else 0,
        "max_degree": max(deg_values) if deg_values else 0,
        "max_degree_node": top_degree_info[0] if top_degree_info else None,
        "top_degree_nodes": top_degree_info,
        "isolated_nodes": len(isolated),
        "num_components": len(components),
        "giant_component_size": giant.number_of_nodes(),
        "giant_component_fraction": round(giant.number_of_nodes() / n, 4) if n else 0,
        "avg_shortest_path_giant_component": round(avg_path, 3),
        "diameter_giant_component_est": diameter,
        "diameter_path_labels": diameter_path_labels,
        "avg_clustering_coefficient": round(clustering, 4),

        # PageRank
        "top_pagerank_nodes": top_pagerank_info,

        # Louvain
        "louvain_num_communities": len(communities),
        "louvain_community_sizes": community_sizes,
        "louvain_modularity": louvain_modularity,

        # Betweenness (sampled)
        "betweenness_sample_size": betweenness_k,
        "avg_betweenness_sampled": round(statistics.mean(betweenness.values()), 6) if betweenness else 0,
        "top_betweenness_nodes": top_betweenness_info,

        # Closeness (sampled)
        "closeness_sample_size": closeness_k,
        "avg_closeness_sampled": round(statistics.mean(closeness.values()), 6) if closeness else 0,
        "top_closeness_nodes": top_closeness_info,
        "degree_assortativity": degree_assortativity,
    }


def print_stats(stats):
    print(f"--- {stats['label']} ---")
    for k, v in stats.items():
        if k in ("label", "top_degree_nodes", "diameter_path_labels"):
            continue
        print(f"{k:35s}: {v}")
    if stats.get("top_degree_nodes"):
        print("top_degree_nodes:")
        for node in stats["top_degree_nodes"]:
            print(f"    {node['degree']:>4d}  {node['id']}  ({node['type']}, label={node['label']})")
    if stats.get("diameter_path_labels"):
        print("diameter_path (words only):")
        print("    " + " -> ".join(str(w) for w in stats["diameter_path_labels"]))
    else:
        print("diameter_path (words only): None")
    print()







_NON_NUMERIC_KEYS = {"label", "max_degree_node", "top_degree_nodes", "diameter_path_labels"}


def plot_stats_series(stats_list, output_dir, title, show=False):
    if not stats_list:
        raise ValueError("stats_list is empty — nothing to plot.")

    os.makedirs(output_dir, exist_ok=True)
    
    X = range(1, len(stats_list["nodes"]) + 1)  # Number of nodes in each graph run
    print(stats_list)
    metric_keys = []
    for k,v in stats_list.items():
        if k in _NON_NUMERIC_KEYS:
            continue
        if isinstance(v[0], (int, float)) and not isinstance(v[0], bool) and k not in metric_keys:
            metric_keys.append(k)

    for stat_name in metric_keys:
        Y = stats_list[stat_name]
        print(f"Plotting {stat_name} vs Cycle Number")
        plt.figure(figsize=(10, 6))
        plt.plot(X, Y, marker='o')
        plt.title(f"{title} - {stat_name} vs Ciclo")
        plt.xlabel("Ciclo")
        plt.ylabel(stat_name)
        plt.grid(True)
        plt.tight_layout()
        output_path = f"{output_dir}/{title}_{stat_name.replace(' ', '_')}.png"
        plt.savefig(output_path)
        if show:
            plt.show()
        plt.close()



def induced_subgraph(G, subset_ids):
    subset_ids = set(subset_ids) & set(G.nodes())
    sub_G = G.subgraph(subset_ids).copy()

    sub_nodes = {nid: dict(sub_G.nodes[nid]) for nid in sub_G.nodes()}
    sub_edges = [{"source": u, "target": v} for u, v in sub_G.edges()]

    return sub_nodes, sub_edges, sub_G


def percentile_of_value(value, population):
    """% of `population` values <= `value`. Returns None if population is empty."""
    if not population:
        return None
    return round(100 * sum(1 for v in population if v <= value) / len(population), 2)


def compare_subset_to_full_graph(
    G, subset_ids, label="subset",
    n_random_samples=100, seed=0,
    metrics_for_null=("density", "avg_degree", "avg_clustering_coefficient",
                       "giant_component_fraction", "num_components"),
):
    subset_ids = list(set(subset_ids) & set(G.nodes()))
    if not subset_ids:
        raise ValueError("None of the given subset_ids exist in the graph.")

    sub_nodes, sub_edges, _ = induced_subgraph(G, subset_ids)
    subset_stats = graph_connectivity_stats(G, label=label)

    full_degrees = [d for _, d in G.degree()]
    degree_percentile = percentile_of_value(subset_stats["avg_degree"], full_degrees)

    random.seed(seed)
    all_ids = list(G.nodes())
    k = min(len(subset_ids), len(all_ids))

    null_metrics = {m: [] for m in metrics_for_null}
    for _ in range(n_random_samples):
        sample_ids = random.sample(all_ids, k)
        s_nodes, s_edges, _ = induced_subgraph(G, sample_ids)
        s_stats = graph_connectivity_stats(G, label="null_sample")
        for m in metrics_for_null:
            null_metrics[m].append(s_stats.get(m, 0))

    percentiles_vs_random = {
        m: percentile_of_value(subset_stats.get(m, 0), pop) for m, pop in null_metrics.items()
    }

    return {
        "subset_stats": subset_stats,
        "degree_percentile_vs_all_nodes": degree_percentile,
        "percentiles_vs_random_subsets": percentiles_vs_random,
        "random_sample_size": n_random_samples,
        "subset_size": k,
    }


def print_comparison(result):
    s = result["subset_stats"]
    print(f"--- {s['label']} ({result['subset_size']} nodes, induced subgraph) ---")
    print(f"avg_degree                 : {s['avg_degree']}  "
          f"(percentile {result['degree_percentile_vs_all_nodes']} vs all individual nodes)")
    print(f"density                     : {s['density']}")
    print(f"avg_clustering_coefficient  : {s['avg_clustering_coefficient']}")
    print(f"giant_component_fraction    : {s['giant_component_fraction']}")
    print(f"num_components              : {s['num_components']}")
    print()
    print(f"Percentiles vs {result['random_sample_size']} random subsets of the same size:")
    for metric, pct in result["percentiles_vs_random_subsets"].items():
        print(f"    {metric:30s}: {pct}th percentile")
    print()




def node_stats_in_full_graph(G, subset_ids):
    all_degrees = [d for _, d in G.degree()]
    nodes = {nid: dict(G.nodes[nid]) for nid in G.nodes()}

    results = []
    missing = []
    for nid in subset_ids:
        if nid not in nodes:
            missing.append(nid)
            continue
        degree = G.degree(nid) if nid in G else 0
        results.append({
            "id": nid,
            "label": nodes[nid].get("label"),
            "type": nodes[nid].get("type"),
            "degree": degree,
            "degree_percentile": percentile_of_value(degree, all_degrees),
            "clustering_coefficient": round(local_clustering_coefficient(nid, G), 4) if nid in G else 0.0,
        })

    if missing:
        print(f"Note: {len(missing)} id(s) not found in the graph: {missing}")

    return results


def print_node_stats(results):
    print(f"{'node id':30s} {'degree':>7s} {'percentile':>11s} {'clustering':>11s}")
    for r in sorted(results, key=lambda x: -x["degree"]):
        print(f"{r['id']:30s} {r['degree']:>7d} {r['degree_percentile']:>10.1f}% {r['clustering_coefficient']:>11.4f}")
    print()


def subset_summary_in_full_graph(G, subset_ids, label="subset"):
    node_results = node_stats_in_full_graph(G, subset_ids)
    if not node_results:
        raise ValueError("None of the given subset_ids were found in the graph.")

    degrees = [r["degree"] for r in node_results]
    avg_degree = statistics.mean(degrees)

    all_degrees = [d for _, d in G.degree()]

    return {
        "label": label,
        "subset_size": len(node_results),
        "avg_degree": round(avg_degree, 3),
        "avg_degree_percentile_vs_all_nodes": percentile_of_value(avg_degree, all_degrees),
        "node_details": node_results,
    }



def get_node_ids_for_words(conn, words, mode="words", language="EN"):
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in words)
    if mode == "words":
        cursor.execute(
            f"SELECT DISTINCT(word) FROM words WHERE language = ? AND CONCEPT IS NULL AND word IN ({placeholders})",
            (language, *words),
        )
    elif mode == "all":
        cursor.execute(
            f"""
            SELECT DISTINCT word, concept
            FROM words
            WHERE language = ?
            AND word IN ({placeholders})
            AND concept IS NOT NULL
            """,
            (language, *words),
        )
    rows = cursor.fetchall()

    node_ids = []
    for row in rows:
        if mode == "all":
            node_ids.append((row['word']+"_"+row['concept']))
        else:
            node_ids.append(row['word'])
    return node_ids
