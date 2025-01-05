from PIL import Image
import networkx as nx
import matplotlib.pyplot as plt


def generate_node_image(node_indices):
    """
    node_indices içindeki her bir indeks için 'images/{idx}.png' dosyasını açar,
    hepsini yan yana birleştirip tek bir PIL.Image nesnesi olarak döndürür.
    """
    image_paths = ["images/%d.png" % idx for idx in node_indices]
    images = [Image.open(x) for x in image_paths]

    # Genişlik ve yükseklikleri hesapla
    widths, heights = zip(*(i.size for i in images))

    total_width = sum(widths)
    max_height = max(heights)

    # Yan yana yapıştırmak için yeni bir "büyük" resim oluştur
    new_im = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]

    # Biraz küçültme: len(node_indices) sayısına göre ölçekle
    new_im = new_im.resize((int(total_width * len(node_indices) / 10),
                            int(max_height * len(node_indices) / 10)))

    return new_im


def generate_split_viz(node_indices, left_indices, right_indices, feature):
    """
    node_indices kümesinden sol(right_indices) ve sağ(left_indices)
    dallarını oluşturan bir karar düğümünü çiz.
    """
    G = nx.DiGraph()

    # Her bir liste için birer düğüm ekliyoruz (0: root, 1: left, 2: right)
    indices_list = [node_indices, left_indices, right_indices]
    for idx, indices in enumerate(indices_list):
        G.add_node(idx, image=generate_node_image(indices))

    # Root -> left, Root -> right okları
    G.add_edge(0, 1)
    G.add_edge(0, 2)

    # -- FARKLI KÜTÜPHANE/LAYOUT -- #
    # graphviz_layout yerine shell_layout kullanıyoruz
    pos = nx.shell_layout(G)
    # Bunun yerine nx.spring_layout(G) veya nx.planar_layout(G) de deneyebilirsiniz.

    fig = plt.figure()
    ax = plt.subplot(111)
    ax.set_aspect('equal')

    # Kenarları çiz
    nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowsize=40)

    # Eksen transformları (resimleri doğru konumlandırmak için)
    trans = ax.transData.transform
    trans2 = fig.transFigure.inverted().transform

    # Feature isimleri (örnek)
    feature_name = ["Brown Cap", "Tapering Stalk Shape", "Solitary"][feature]
    ax_name = [
        "Splitting on %s" % feature_name,
        "Left: %s = 1" % feature_name,
        "Right: %s = 0" % feature_name
    ]

    # Her bir düğümü, orada toplanan resimlerle birlikte çiz
    for idx, n in enumerate(G):
        xx, yy = trans(pos[n])  # figure coordinates
        xa, ya = trans2((xx, yy))  # axes coordinates
        piesize = len(indices_list[idx]) / 9
        p2 = piesize / 2.0

        # Her düğüm için ayrı bir "axes" açıp orada resmi gösteriyoruz
        a = plt.axes([xa - p2, ya - p2, piesize, piesize])
        a.set_aspect('equal')
        a.imshow(G.nodes[n]['image'])
        a.axis('off')
        a.set_title(ax_name[idx])

    ax.axis('off')
    plt.show()


def generate_tree_viz(root_indices, y, tree):
    """
    Basit bir karar ağacı görselleştirmesi.
    `tree` parametresi, her seviyede
      (left_indices, right_indices, split_feature)
    şeklinde bilgi içeriyor varsayımıyla hareket eder.
    """
    G = nx.DiGraph()

    # İlk düğüm (root)
    G.add_node(0, image=generate_node_image(root_indices))
    idx = 1
    root = 0

    num_images = [len(root_indices)]

    feature_name = ["Brown Cap", "Tapering Stalk Shape", "Solitary"]
    y_name = ["Poisonous", "Edible"]

    decision_names = []
    leaf_names = []

    # `tree` ile gezinerek her split adımında düğümler ekliyoruz
    for i, level in enumerate(tree):
        # level = [left_indices, right_indices, split_feature]
        indices_list = level[:2]
        split_feat = level[2]

        for indices in indices_list:
            G.add_node(idx, image=generate_node_image(indices))
            G.add_edge(root, idx)

            # Görselleştirme için
            num_images.append(len(indices))
            idx += 1

            # i > 0 ise (root haricinde ise) bir "leaf" olabilir diye ek örnek:
            if i > 0:
                # max(y[indices]) -> Bu sadece basit bir örnek
                leaf_names.append("Leaf node: %s" % y_name[max(y[indices])])

        decision_names.append("Split on: %s" % feature_name[split_feat])
        root += 1

    # Karar düğümlerinin isimleri + yaprak isimleri
    node_names = decision_names + leaf_names

    # -- FARKLI KÜTÜPHANE/LAYOUT -- #
    pos = nx.shell_layout(G)
    # Alternatif olarak: pos = nx.spring_layout(G) veya nx.planar_layout(G)

    fig = plt.figure(figsize=(14, 10))
    ax = plt.subplot(111)
    ax.set_aspect('equal')

    # Kenarları çiz
    nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowsize=40)

    trans = ax.transData.transform
    trans2 = fig.transFigure.inverted().transform

    # Her düğümün resmini ilgili konuma yerleştiriyoruz
    for i_node, n in enumerate(G):
        xx, yy = trans(pos[n])  # figure coordinates
        xa, ya = trans2((xx, yy))  # axes coordinates

        # Kaç resim var ise "piesize" biraz orantılı büyüklükte olsun
        piesize = num_images[i_node] / 25
        p2 = piesize / 2.0

        a = plt.axes([xa - p2, ya - p2, piesize, piesize])
        a.set_aspect('equal')
        a.imshow(G.nodes[n]['image'])
        a.axis('off')

        # node_names listesini sırasıyla başlık olarak yazalım (index hatasına dikkat)
        if i_node < len(node_names):
            a.set_title(node_names[i_node], y=-0.8, fontsize=13, loc="left")

    ax.axis('off')
    plt.show()
