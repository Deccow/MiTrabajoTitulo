import random
import statistics

import networkx as nx

import graph_stats as gs



def analyze_word_group(G, node_ids, label="group", mode="words", language="EN"):
    """
    Analyze a collection of graph node IDs.

    Parameters
    ----------
    G : nx.Graph
    node_ids : iterable
        Graph node IDs.
    """

    if mode == "words":        
        node_ids = [n+language for n in node_ids if G.has_node(n+language)]
    elif mode == "all":
        node_ids = [n for n in node_ids if G.has_node(n)]
    
    if not node_ids:
        raise ValueError("None of the given node IDs exist in the graph.")

    all_details = gs.node_stats_in_full_graph(G, node_ids)

    degrees = [d["degree"] for d in all_details]

    all_degrees = [deg for _, deg in G.degree()]

    aggregate = {
        "n_nodes": len(all_details),
        "degree_mean": round(statistics.mean(degrees), 3),
        "degree_median": statistics.median(degrees),
        "degree_stdev": round(statistics.stdev(degrees), 3)
        if len(degrees) > 1 else 0.0,
        "degree_mean_percentile_vs_all_nodes":
            gs.percentile_of_value(statistics.mean(degrees), all_degrees),
    }

    return {
        "label": label,
        "flat_node_details": all_details,
        "aggregate": aggregate,
    }


def print_word_group_analysis(result):

    agg = result["aggregate"]

    print(f"=== {result['label']} ===")
    print(f"Nodes analyzed: {agg['n_nodes']}")
    print()
    print(
        f"Degree mean={agg['degree_mean']:.3f} "
        f"median={agg['degree_median']} "
        f"stdev={agg['degree_stdev']:.3f}"
    )
    print(
        f"Mean degree percentile: "
        f"{agg['degree_mean_percentile_vs_all_nodes']}"
    )
    print()


def group_removal_vitality(
    G,
    subset_ids,
    label="group",
    n_random_samples=100,
    seed=0,
):

    subset_ids = [n for n in subset_ids if G.has_node(n)]

    if not subset_ids:
        raise ValueError("No valid nodes.")

    baseline = gs.graph_connectivity_stats(G, label="baseline")

    all_nodes = list(G.nodes())

    def removal_effect(remove_nodes):

        remaining = set(G.nodes()) - set(remove_nodes)

        H = G.subgraph(remaining).copy()

        after = gs.graph_connectivity_stats(H)

        return {

            "giant_component_fraction_drop":
                baseline["giant_component_fraction"]
                - after["giant_component_fraction"],

            "avg_shortest_path_change":
                after["avg_shortest_path_giant_component"]
                - baseline["avg_shortest_path_giant_component"],

            "num_components_increase":
                after["num_components"]
                - baseline["num_components"],
        }

    group_effect = removal_effect(subset_ids)

    random.seed(seed)

    k = len(subset_ids)

    null = {
        "giant_component_fraction_drop": [],
        "avg_shortest_path_change": [],
        "num_components_increase": [],
    }

    for _ in range(n_random_samples):

        sample = random.sample(all_nodes, k)

        effect = removal_effect(sample)

        for metric in null:
            null[metric].append(effect[metric])

    percentiles = {
        metric: gs.percentile_of_value(group_effect[metric], values)
        for metric, values in null.items()
    }

    return {

        "label": label,

        "group_size": k,

        "baseline_giant_component_fraction":
            baseline["giant_component_fraction"],

        "baseline_avg_shortest_path":
            baseline["avg_shortest_path_giant_component"],

        "group_removal_effect":
            group_effect,

        "percentiles_vs_random_removal":
            percentiles,

        "random_sample_size":
            n_random_samples,
    }


def print_vitality(result):

    eff = result["group_removal_effect"]
    pct = result["percentiles_vs_random_removal"]

    print(
        f"--- {result['label']} "
        f"({result['group_size']} nodes removed) ---"
    )

    print(
        f"Giant component drop : "
        f"{eff['giant_component_fraction_drop']:+.4f} "
        f"(p{pct['giant_component_fraction_drop']})"
    )

    print(
        f"Average shortest path : "
        f"{eff['avg_shortest_path_change']:+.4f} "
        f"(p{pct['avg_shortest_path_change']})"
    )

    print(
        f"Components increase : "
        f"{eff['num_components_increase']} "
        f"(p{pct['num_components_increase']})"
    )

    print()






def full_word_group_report(
    conn,
    words,
    language="EN",
    n_random_samples=100,
    seed=0,
):

    from ..GraphBrowserAPP import graph as g

    word_to_ids = gs.get_node_ids_for_words(
        conn,
        words,
        language=language,
    )

    G = g.build_full_graph(conn)

    node_ids = []

    for ids in word_to_ids.values():
        node_ids.extend(ids)

    analysis = analyze_word_group(
        G,
        node_ids,
        label="word group",
    )

    print_word_group_analysis(analysis)

    vitality = group_removal_vitality(
        G,
        node_ids,
        label="word group",
        n_random_samples=n_random_samples,
        seed=seed,
    )

    print_vitality(vitality)

    return {
        "analysis": analysis,
        "vitality": vitality,
    }
from networkx.algorithms.structuralholes import constraint

def core_word_metrics(G: nx.Graph, words, mode="words", language="EN"):

    if words is None:
        words = []

    if mode == "words":
        words = [w + language for w in words if G.has_node(w + language)]
    elif mode == "all":
        words = [w for w in words if G.has_node(w)]

    

    # print("Computing Degree...")
    degree = dict(G.degree())

    # print("Computing Eigenvector...")
    eigenvector = nx.eigenvector_centrality(
        G,
        max_iter=1000,
        tol=1e-6,
    )

    # print("Computing PageRank...")
    pagerank = nx.pagerank(G)

    # print("Computing k-core numbers...")
    core_numbers = nx.core_number(G)
    max_core = max(core_numbers.values())

    # print("Computing clustering coefficients...")
    clustering = nx.clustering(G)

    # print("Computing triangle counts...")
    triangles = nx.triangles(G)

    # print("Computing average neighbor degree...")
    avg_neighbor_degree = nx.average_neighbor_degree(G)

    # print("Computing neighborhood statistics...")

    # print("Computing approximate betweenness centrality...")
    betweenness = nx.betweenness_centrality(
        G,
        k=500,    
        seed=0,  
    )

    print("Computing Louvain communities...")
    louvain_communities = nx.community.louvain_communities(G, seed=0)
    # louvain_communities es una lista de sets de nodos; se transforma
    # a un diccionario {nodo: id_comunidad} y {nodo: tamaño_comunidad}
    node_to_community = {}
    community_size = {}
    for community_id, community_nodes in enumerate(louvain_communities):
        for node in community_nodes:
            node_to_community[node] = community_id
            community_size[node] = len(community_nodes)

    # mean_neighbor_core = {}
    # frac_neighbors_max_core = {}
    # mean_neighbor_pagerank = {}

    # for node in G.nodes():

    #     neighbors = list(G.neighbors(node))

    #     if neighbors:

    #         mean_neighbor_core[node] = statistics.mean(
    #             core_numbers[n] for n in neighbors
    #         )

    #         mean_neighbor_pagerank[node] = statistics.mean(
    #             pagerank[n] for n in neighbors
    #         )

    #         frac_neighbors_max_core[node] = (
    #             sum(core_numbers[n] == max_core for n in neighbors)
    #             / len(neighbors)
    #         )

    #     else:

    #         mean_neighbor_core[node] = 0.0
    #         mean_neighbor_pagerank[node] = 0.0
    #         frac_neighbors_max_core[node] = 0.0

    results = {}

    for word in G.nodes():

        results[word] = {

            "degree": degree[word],
            "eigenvector": eigenvector[word],
            "pagerank": pagerank[word],
            "betweenness": betweenness[word],
            "k_core": core_numbers[word],

            "clustering": clustering[word],

            "triangles": triangles[word],

            "average_neighbor_degree":
                avg_neighbor_degree[word],

            
            "louvain_community_id":
                node_to_community[word],

            "louvain_community_size":
                community_size[word],

            # "mean_neighbor_core":
            #     mean_neighbor_core[word],

            # "fraction_neighbors_max_core":
            #     frac_neighbors_max_core[word],

            # "mean_neighbor_pagerank":
            #     mean_neighbor_pagerank[word],
        }

    other_nodes = set(G.nodes()) - set(words)

    def summarize(metric_dict):
        words_vals = [metric_dict[w] for w in words if metric_dict[w] is not None]
        other_vals = [metric_dict[n] for n in other_nodes if metric_dict[n] is not None]

        return {
            "words_mean": statistics.mean(words_vals) if words_vals else None,
            "words_median": statistics.median(words_vals) if words_vals else None,
            "graph_mean_excluding_words": (
                statistics.mean(other_vals) if other_vals else None
            ),
            "graph_median_excluding_words": (
                statistics.median(other_vals) if other_vals else None
            ),
        }

    summary = {

        "degree": summarize(degree),

        "eigenvector": summarize(eigenvector),

        "pagerank": summarize(pagerank),

        "k_core": summarize(core_numbers),

        "clustering": summarize(clustering),

        "triangles": summarize(triangles),

        "betweenness": summarize(betweenness),

        "average_neighbor_degree":
            summarize(avg_neighbor_degree),

        "louvain_community_size":
            summarize(community_size),

        # "mean_neighbor_core":
        #     summarize(mean_neighbor_core),

        # "fraction_neighbors_max_core":
        #     summarize(frac_neighbors_max_core),

        # "mean_neighbor_pagerank":
        #     summarize(mean_neighbor_pagerank),

    }

    summary["louvain_num_communities"] = len(louvain_communities)
    summary["louvain_modularity"] = nx.community.modularity(G, louvain_communities)


    percentile_metrics = {

        "degree": degree,

        "eigenvector": eigenvector,

        "pagerank": pagerank,

        "k_core": core_numbers,

        "clustering": clustering,

        "triangles": triangles,

        "betweenness": betweenness,

        "average_neighbor_degree":
            avg_neighbor_degree,

        # "mean_neighbor_core":
        #     mean_neighbor_core,

        # "fraction_neighbors_max_core":
        #     frac_neighbors_max_core,

        # "mean_neighbor_pagerank":
        #     mean_neighbor_pagerank,
        "louvain_community_size":
            community_size,
    }

    for name, metric in percentile_metrics.items():

        # se filtran los None (relevante sobre todo para closeness, que es muestreado)
        reference_values = [v for v in metric.values() if v is not None]

        if summary[name]["words_mean"] is not None:
            summary[f"{name}_mean_percentile"] = gs.percentile_of_value(
                summary[name]["words_mean"],
                reference_values
            )
        if summary[name]["words_median"] is not None:
            summary[f"{name}_median_percentile"] = gs.percentile_of_value(
                summary[name]["words_median"],
                reference_values
            )


    for name, metric in percentile_metrics.items():

        summary[f"{name}_list"] = sorted(
            metric.items(),
            key=lambda x: x[1],
            reverse=True,
        )

    for name, metric in percentile_metrics.items():

        summary[f"{name}_list_unsorted"] = metric.items()
    return {
        "node_metrics": results,
        "summary": summary,
        "louvain_communities": louvain_communities,
    }


