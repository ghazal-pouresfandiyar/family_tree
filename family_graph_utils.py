import html
from collections import deque


def person_sort_key(person):
    return (person.name.lower(), int(person.person_id))


def label_fontname():
    return "Helvetica-Bold"


def image_fontsize(tree):
    return str(min(255, max(72, round(tree.image_node_height * 28))))


def highlighted_label(tree, text):
    safe_text = html.escape(text)
    return (
        '<<TABLE BORDER="0" CELLBORDER="1" CELLPADDING="7" BGCOLOR="white">'
        f'<TR><TD><FONT FACE="{label_fontname()}" POINT-SIZE="{image_fontsize(tree)}" COLOR="black">{safe_text}</FONT></TD></TR>'
        "</TABLE>>"
    )


def highlighted_red_label(text, point_size=160):
    safe_text = html.escape(text)
    return (
        '<<TABLE BORDER="0" CELLBORDER="1" CELLPADDING="6" BGCOLOR="#ff2a2a">'
        f'<TR><TD><FONT FACE="{label_fontname()}" POINT-SIZE="{point_size}" COLOR="black"><B>{safe_text}</B></FONT></TD></TR>'
        "</TABLE>>"
    )


def compute_generations(tree):
    levels = {}
    people_sorted = sorted(tree.people.values(), key=person_sort_key)

    if not people_sorted:
        return levels

    starts = []
    if tree.root is not None:
        starts.append(tree.root)
    starts.extend(p for p in people_sorted if p is not tree.root)

    for candidate in starts:
        node_id = tree._node_id(candidate)
        if node_id in levels:
            continue

        queue = deque([(candidate, 0 if not levels else max(levels.values()) + 2)])
        while queue:
            person, level = queue.popleft()
            node_id = tree._node_id(person)
            existing = levels.get(node_id)
            if existing is not None and existing <= level:
                continue

            levels[node_id] = level

            if person.partner is not None:
                queue.append((person.partner, level))

            for child in sorted(person.children, key=person_sort_key):
                queue.append((child, level + 1))

    return levels


def collect_family_units(tree, people_sorted):
    units = {}

    for person in people_sorted:
        if person.partner is not None:
            parent_pair = tuple(sorted([person, person.partner], key=person_sort_key))
        else:
            parent_pair = (person,)

        key = tuple(tree._node_id(p) for p in parent_pair)
        if key not in units:
            units[key] = {"parents": list(parent_pair), "children": []}

        for child in person.children:
            if child not in units[key]["children"]:
                units[key]["children"].append(child)

    ordered = []
    for _, data in units.items():
        parents = sorted(data["parents"], key=person_sort_key)
        children = list(data["children"])
        ordered.append((parents, children))

    ordered.sort(key=lambda item: tuple(person_sort_key(p) for p in item[0]))
    return ordered


def family_colors():
    return [
        "#c0392b",
        "#2980b9",
        "#27ae60",
        "#8e44ad",
        "#d35400",
        "#16a085",
        "#2c3e50",
        "#7f8c8d",
    ]


def add_people_nodes(graph, tree, people_sorted, family_units, colors, image_manager):
    sibling_border_colors = {}
    for family_index, (_, children) in enumerate(family_units):
        family_color = colors[family_index % len(colors)]
        for child in children:
            sibling_border_colors[tree._node_id(child)] = family_color

    for person in people_sorted:
        image_path = image_manager.choose_image(person)
        node_id = tree._node_id(person)
        label_text = person.name if person.person_id == 1 else f"{person.name} ({person.person_id})"
        border_color = sibling_border_colors.get(node_id, "#555555")
        border_width = 52 if node_id in sibling_border_colors else 12

        if image_path:
            rounded_image = image_manager.rounded_image_path(image_path, border_color, border_width)
            image_width, image_height = image_manager.image_render_size(rounded_image)
            caption_size = max(110, min(255, int(float(image_height) * 4)))
            graph.node(
                node_id,
                label=highlighted_red_label(label_text, caption_size),
                labelloc="b",
                imagepos="tc",
                image=rounded_image,
                imagescale="both",
                fixedsize="false",
                shape="box",
                style="rounded,filled",
                fontname=label_fontname(),
                color=border_color,
                penwidth=str(border_width),
                width=image_width,
                height=image_height,
                margin="0.01",
            )
        else:
            label = highlighted_red_label(label_text, 220)
            graph.node(node_id, label=label, shape="box", style="filled", color="#555555", penwidth="12")


def add_partner_edges(graph, tree, people_sorted):
    seen = set()
    for person in people_sorted:
        if not person.partner:
            continue

        pair = tuple(sorted([tree._node_id(person), tree._node_id(person.partner)]))
        if pair in seen:
            continue

        with graph.subgraph(name=f"spouse_rank_{pair[0]}_{pair[1]}") as spouse_rank:
            spouse_rank.attr(rank="same")
            spouse_rank.node(pair[0])
            spouse_rank.node(pair[1])

        graph.edge(
            pair[0],
            pair[1],
            dir="none",
            color="#444444",
            constraint="true",
            weight="520",
            minlen="1",
            penwidth="20",
            len="0.25",
        )
        seen.add(pair)


def add_family_edges(graph, tree, family_units, colors):
    for family_index, (parents, children) in enumerate(family_units):
        if not children:
            continue

        family_group = f"family_{family_index}"
        family_color = colors[family_index % len(colors)]
        family_anchor_id = f"family_anchor_{family_index}"
        marriage_id = f"marriage_{family_index}"
        junction_ids = []

        with graph.subgraph(name=f"cluster_family_{family_index}") as family_cluster:
            family_cluster.attr(
                label="",
                color=family_color,
                penwidth="4",
                style="rounded",
                margin="4",
            )
            family_cluster.node(
                family_anchor_id,
                label="",
                shape="point",
                width="0.01",
                height="0.01",
                style="invis",
            )

            family_cluster.node(
                marriage_id,
                label="",
                shape="point",
                width="0.04",
                height="0.04",
                style="filled",
                fillcolor=family_color,
                color=family_color,
                group=family_group,
            )
            family_cluster.edge(
                family_anchor_id,
                marriage_id,
                style="invis",
                constraint="false",
            )

            with graph.subgraph(name=f"family_parent_rank_{family_index}") as parent_rank:
                parent_rank.attr(rank="same")
                for parent in parents:
                    parent_rank.node(tree._node_id(parent))

            for parent in parents:
                parent_id = tree._node_id(parent)
                graph.node(parent_id, group=family_group)
                graph.edge(
                    parent_id,
                    marriage_id,
                    color=family_color,
                    constraint="true",
                    weight="90",
                    minlen="3",
                )

            for child_index, child in enumerate(children):
                junction_id = f"sib_junction_{family_index}_{child_index}"
                junction_ids.append(junction_id)
                family_cluster.node(
                    junction_id,
                    label="",
                    shape="point",
                    width="0.03",
                    height="0.03",
                    style="filled",
                    fillcolor=family_color,
                    color=family_color,
                    group=family_group,
                )

            with family_cluster.subgraph(name=f"family_junction_rank_{family_index}") as junction_rank:
                junction_rank.attr(rank="same")
                for junction_id in junction_ids:
                    junction_rank.node(junction_id)

            middle_index = len(junction_ids) // 2
            family_cluster.edge(
                marriage_id,
                junction_ids[middle_index],
                color=family_color,
                constraint="true",
                weight="300",
                minlen="1",
            )

            if len(junction_ids) > 1:
                for i in range(len(junction_ids) - 1):
                    family_cluster.edge(
                        junction_ids[i],
                        junction_ids[i + 1],
                        dir="none",
                        color=family_color,
                        constraint="true",
                        weight="170",
                        minlen="1",
                    )

            base_n = max(1, len(children) - 1)
            child_drop_base = max(1, int(round(base_n / 32)))
            for child_index, child in enumerate(children):
                child_id = tree._node_id(child)
                graph.node(child_id, group=family_group)
                drop_len = str((child_index + 1) * child_drop_base)
                graph.edge(
                    junction_ids[child_index],
                    child_id,
                    color=family_color,
                    constraint="true",
                    weight="310",
                    minlen=drop_len,
                )
