from graphviz import Digraph

from family_graph_utils import (
    add_family_edges,
    add_partner_edges,
    add_people_nodes,
    collect_family_units,
    family_colors,
    image_fontsize,
    label_fontname,
    person_sort_key,
)


class GraphBuilder:
    def __init__(self, image_manager):
        self.image_manager = image_manager

    def build_graph(self, tree):
        graph = Digraph("FamilyTree", format="png", engine="dot")
        graph.attr(
            rankdir="TB",
            newrank="true",
            splines="ortho",
            concentrate="false",
            ordering="out",
            forcelabels="true",
            compound="true",
            pack="true",
            packmode="clust",
            bgcolor="white",
            pad="0.7",
            margin="0.3",
        )
        graph.attr(nodesep="0.25", ranksep="0.8 equally")
        graph.attr(
            "node",
            shape="box",
            style="rounded,filled",
            fillcolor="lightyellow",
            fontname=label_fontname(),
            fontsize=image_fontsize(tree),
        )
        graph.attr("edge", color="black", arrowhead="none", penwidth="20")

        people_sorted = sorted(tree.people.values(), key=person_sort_key)
        family_units = collect_family_units(tree, people_sorted)
        colors = family_colors()

        add_people_nodes(graph, tree, people_sorted, family_units, colors, self.image_manager)
        add_partner_edges(graph, tree, people_sorted)
        add_family_edges(graph, tree, family_units, colors)

        return graph

    def export_png(self, tree, output_name="family_tree"):
        graph = self.build_graph(tree)
        return graph.render(output_name, cleanup=True)
