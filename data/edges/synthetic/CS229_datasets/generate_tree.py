import networkx as nx
import matplotlib.pyplot as plt

# # r (int) – Branching factor of the tree
# # h (int) – Height of the tree

# # branch_factor = 5
# # height = 5
# # G = nx.balanced_tree(r=branch_factor, h=height)

# num_nodes = 400
# probs = [0.25, 0.5, 0.75, 1]

# for prob in probs:
#     G = nx.erdos_renyi_graph(num_nodes, prob)
#     density = round(nx.density(G), 5)

#     filename = '/Users/shawn/Documents/GitHub/hyperbolics/data/edges/synthetic/CS229_datasets/random_graph_nodes' + str(num_nodes) + '_prob' + str(prob) + '_d' + str(density)
#     nx.write_edgelist(G, filename + '.edges', data=False)
#     # nx.draw_kamada_kawai(G)
#     # plt.savefig("/Users/shawn/Documents/GitHub/hyperbolics/data/edges/synthetic/CS229_datasets/plots/" + filename + ".png", dpi=200)
    
# "/Users/shawn/Documents/GitHub/hyperbolics/data/edges/phylo_tree.edges"

G = nx.read_edgelist("/Users/shawn/Documents/GitHub/hyperbolics/data/edges/synthetic/sierp-K4-5.edges")
# G = nx.les_miserables_graph()
# G = nx.convert_node_labels_to_integers(G)
# filename = '/Users/shawn/Documents/GitHub/hyperbolics/data/edges/synthetic/CS229_datasets/les_mis'
# nx.write_edgelist(G, filename + '.edges', data=False)
nx.draw_kamada_kawai(G)
plt.show()
# plt.savefig("/Users/shawn/Documents/GitHub/hyperbolics/data/edges/synthetic/CS229_datasets/plots/les_mis" + ".png", dpi=200)