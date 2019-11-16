import networkx as nx
import matplotlib.pyplot as plt

# r (int) – Branching factor of the tree
# h (int) – Height of the tree

branch_factor = 5
height = 5

G = nx.balanced_tree(r=branch_factor, h=height)
density = round(nx.density(G), 5)

filename = 'balanced_tree_r' + str(branch_factor) + '_h' + str(height) + '_d' + str(density) + '.edges'
nx.write_edgelist(G, filename, data=False)
nx.draw_kamada_kawai(G)
plt.savefig("/plots/" + filename + ".png", dpi=200)