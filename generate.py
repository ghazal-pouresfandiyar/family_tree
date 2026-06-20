#!/usr/bin/env python3
"""Generate family tree HTML from tree.txt"""

import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
TREE_FILE = BASE_DIR / "tree.txt"
OUTPUT_FILE = BASE_DIR / "index.html"

COLORS = [
    "#c07b8a", "#7ba5c4", "#8bc47b", "#c4a87b", "#b07bc4",
    "#c47b7b", "#7bc4b8", "#c4c07b", "#7b8fc4",
    "#c49b7b", "#7bc4a8", "#a87bc4", "#c47ba8", "#7bafc4",
    "#c4b87b", "#8ac47b", "#c47b4f"
]


def parse_name(raw):
    """Parse 'Name' or 'Name ID' -> (name, id_or_None)"""
    parts = raw.strip().split()
    if len(parts) >= 2 and parts[-1].isdigit():
        return parts[0], parts[-1]
    return parts[0], None


def parse_children(raw):
    """Parse 'Name1, Name2 m, Name3 ID' -> [(name, id_or_None), ...]"""
    if raw.strip() == '0':
        return []
    result = []
    for c in raw.split(','):
        c = c.strip()
        if not c:
            continue
        parts = c.split()
        name = parts[0]
        cid = None
        if len(parts) >= 2 and parts[-1] not in ('m', 'f') and parts[-1].isdigit():
            cid = parts[-1]
        result.append((name, cid))
    return result


def build_tree(text):
    """Parse tree.txt and build nested tree structure."""
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]

    # Parse all lines into marriages list
    marriages = []
    root_children_raw = None

    for i, line in enumerate(lines):
        m = re.match(r'(.+?)\s*&\s*(.+?)\s*:\s*(.+)', line)
        if not m:
            continue
        p1, p1_id = parse_name(m.group(1))
        p2, p2_id = parse_name(m.group(2))
        children = parse_children(m.group(3))
        marriages.append({
            "p1": p1, "p1_id": p1_id,
            "p2": p2, "p2_id": p2_id,
            "children": children
        })
        if i == 0:
            root_children_raw = children

    root = [marriages[0]["p1"], marriages[0]["p2"]]

    # Build index: (name, id) -> list of marriage indices where this person is a CHILD
    # This tells us which marriage produced this person
    child_of = {}  # (name, id) -> marriage_index
    for idx, mar in enumerate(marriages):
        for child_name, child_id in mar["children"]:
            key = (child_name, child_id)
            if key not in child_of:
                child_of[key] = idx

    # Build index: (name, id) -> marriage index where this person is a PARENT
    parent_in = {}  # (name, id) -> marriage_index
    for idx, mar in enumerate(marriages):
        k1 = (mar["p1"], mar["p1_id"])
        k2 = (mar["p2"], mar["p2_id"])
        if k1 not in parent_in:
            parent_in[k1] = idx
        if k2 not in parent_in:
            parent_in[k2] = idx

    def get_parent_id(child_name):
        """Get the ID assigned to a child in their parent's marriage."""
        for idx, mar in enumerate(marriages):
            for cn, cid in mar["children"]:
                if cn == child_name:
                    return cid
        return None

    def build_node(name, parent_id):
        """Build tree node for a person."""
        # Find marriage where this person is a parent
        key = (name, parent_id)
        mar_idx = parent_in.get(key)

        # Also try with None ID (for people who appear without explicit ID in marriage)
        if mar_idx is None:
            # Try finding any marriage where this name appears as parent with any ID
            for midx, mar in enumerate(marriages):
                if (mar["p1"] == name or mar["p2"] == name):
                    # Check if the ID matches
                    if mar["p1"] == name and mar["p1_id"] == parent_id:
                        mar_idx = midx
                        break
                    elif mar["p2"] == name and mar["p2_id"] == parent_id:
                        mar_idx = midx
                        break

        if mar_idx is None:
            # Not a parent, leaf node
            if parent_id:
                return {"p": [name, parent_id], "c": []}
            return {"p": [name], "c": []}

        mar = marriages[mar_idx]
        spouse = mar["p2"] if mar["p1"] == name else mar["p1"]
        spouse_id = mar["p2_id"] if mar["p1"] == name else mar["p1_id"]

        # Build couple array
        if parent_id:
            p_arr = [name, parent_id, spouse]
        elif spouse_id:
            p_arr = [name, spouse, spouse_id]
        else:
            p_arr = [name, spouse]

        # Build children
        children_nodes = []
        for child_name, child_id in mar["children"]:
            children_nodes.append(build_node(child_name, child_id))

        return {"p": p_arr, "c": children_nodes}

    def build_branch(child_name, child_id):
        """Build a branch for a root child."""
        # Find marriage where this person is a parent
        key = (child_name, child_id)
        mar_idx = parent_in.get(key)

        if mar_idx is None:
            return {"main": [child_name], "siblings": []}

        mar = marriages[mar_idx]
        spouse = mar["p2"] if mar["p1"] == child_name else mar["p1"]
        main_arr = [child_name, spouse]

        siblings = []
        for cn, cid in mar["children"]:
            siblings.append(build_node(cn, cid))

        return {"main": main_arr, "siblings": siblings}

    # Build branches for root children
    rc_name1 = root_children_raw[0][0]
    rc_id1 = root_children_raw[0][1]
    rc_name2 = root_children_raw[1][0]
    rc_id2 = root_children_raw[1][1]

    branch1 = build_branch(rc_name1, rc_id1)
    branch1["title"] = f"{rc_name1.replace('_', ' ')}'s Family"
    branch1["sub"] = f"The descendants of {rc_name1.replace('_', ' ')} & {branch1['main'][1].replace('_', ' ')}"

    branch2 = build_branch(rc_name2, rc_id2)
    branch2["title"] = f"{rc_name2.replace('_', ' ')}'s Family"
    branch2["sub"] = f"The descendants of {rc_name2.replace('_', ' ')} & {branch2['main'][1].replace('_', ' ')}"

    # Find cross-branch marriages
    b1_names = set()
    b2_names = set()
    for s in branch1["siblings"]:
        b1_names.add(s["p"][0])
    for s in branch2["siblings"]:
        b2_names.add(s["p"][0])

    cross_branch = []
    for mar in marriages:
        p1, p2 = mar["p1"], mar["p2"]
        if (p1 in b1_names and p2 in b2_names) or (p2 in b1_names and p1 in b2_names):
            cross_branch.append((p1, p2))

    return {
        "root": root,
        "branches": [branch1, branch2],
        "crossBranchMarriages": cross_branch
    }


def generate_html(tree_data):
    tree_json = json.dumps(tree_data, indent=2)
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Family Tree — Roghaye & Yousef</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Georgia', 'Palatino', 'Times New Roman', serif;
    background: #fdf8ed;
    color: #372314;
    line-height: 1.6;
  }}

  .hero {{
    text-align: center;
    padding: 12px 20px 8px;
    background: linear-gradient(135deg, #fdf8ed 0%, #f5e6c8 100%);
    border-bottom: 3px solid #c3a578;
  }}
  .hero h1 {{ font-size: clamp(20px, 4vw, 32px); color: #694128; font-weight: normal; letter-spacing: 2px; margin-bottom: 4px; }}
  .hero .subtitle {{ font-size: clamp(14px, 2.5vw, 20px); color: #8c6e50; font-style: italic; }}
  .hero .ornament {{ font-size: 24px; color: #c3a578; margin-top: 12px; }}
  .scroll-hint {{ font-size: 12px; color: #a08060; margin-top: 8px; font-style: italic; }}

  .root-wrapper {{ text-align: center; padding: 36px 20px 16px; opacity: 0; transform: translateY(30px); transition: opacity 0.8s ease, transform 0.8s ease; }}
  .root-wrapper.visible {{ opacity: 1; transform: translateY(0); }}
  .root-card {{ display: inline-block; background: #fff; border: 2px solid #c3a578; border-radius: 18px; padding: 10px 20px 8px; box-shadow: 0 6px 24px rgba(105,65,40,0.1); background: linear-gradient(to bottom, #fff, #fdf8ed); }}
  .sibling-note {{ font-size: 13px; color: #8c6e50; margin-top: 12px; font-style: italic; }}

  .branch-section {{ padding: 16px 0 32px; opacity: 0; transform: translateY(30px); transition: opacity 0.8s ease, transform 0.8s ease; }}
  .branch-section.visible {{ opacity: 1; transform: translateY(0); }}
  .branch-title {{ text-align: center; font-size: clamp(20px, 3.5vw, 30px); color: #694128; margin-bottom: 4px; font-weight: normal; letter-spacing: 1px; }}

  .branch-couple-card {{ display: inline-block; background: #fff; border: 2px solid #c3a578; border-radius: 18px; padding: 20px 28px 16px; text-align: center; box-shadow: 0 6px 24px rgba(105,65,40,0.1); background: linear-gradient(to bottom, #fff, #fdf8ed); margin-bottom: 12px; }}
  .branch-couple-card .branch-sub {{ font-size: clamp(12px, 1.8vw, 14px); color: #a08060; margin-top: 4px; font-style: italic; }}

  .vline {{ width: 2px; height: 16px; background: #c3a578; margin: 0 auto; }}
  .vline-sm {{ width: 2px; height: 8px; margin: 0 auto; }}

  .marriage-connector {{ text-align: center; padding: 20px 16px; margin: 0 auto; max-width: 500px; }}
  .marriage-connector .connector-line {{ display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 8px; }}
  .marriage-connector .connector-bar {{ flex: 1; max-width: 120px; height: 2px; background: linear-gradient(90deg, transparent, #c3a578, transparent); }}
  .marriage-connector .connector-icon {{ font-size: 18px; color: #c47b8a; flex-shrink: 0; }}
  .marriage-connector .connector-names {{ font-size: 14px; color: #694128; font-weight: bold; margin-bottom: 4px; }}
  .marriage-connector .connector-label {{ font-size: 12px; color: #a08060; font-style: italic; }}

  .siblings-scroll {{ overflow-x: auto; overflow-y: visible; padding: 0 40px; -webkit-overflow-scrolling: touch; scrollbar-width: thin; scrollbar-color: #c3a578 #f0e6d3; }}
  .siblings-scroll::-webkit-scrollbar {{ height: 8px; }}
  .siblings-scroll::-webkit-scrollbar-track {{ background: #f0e6d3; border-radius: 4px; }}
  .siblings-scroll::-webkit-scrollbar-thumb {{ background: #c3a578; border-radius: 4px; }}
  .siblings-row {{ display: inline-flex; gap: 16px; padding: 4px 8px; flex-wrap: nowrap; }}

  .sibling-col {{ display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }}

  .kids-scroll {{ overflow-x: auto; overflow-y: hidden; padding: 2px 4px; max-width: 100%; }}
  .kids-scroll::-webkit-scrollbar {{ height: 4px; }}
  .kids-scroll::-webkit-scrollbar-thumb {{ background: #c3a578; border-radius: 2px; }}
  .kids-row {{ display: inline-flex; gap: 8px; flex-wrap: nowrap; }}

  .child-subtree {{ display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }}

  .family-card {{ background: #fff; border-radius: 14px; padding: 14px 12px 10px; text-align: center; box-shadow: 0 3px 16px rgba(105,65,40,0.07); border: 2px solid #e8ddd0; transition: transform 0.3s ease, box-shadow 0.3s ease; flex-shrink: 0; }}
  .family-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 24px rgba(105,65,40,0.13); }}

  .couple-row {{ display: flex; align-items: center; justify-content: center; gap: 5px; margin-bottom: 2px; }}
  .person {{ text-align: center; display: inline-block; }}
  .person img {{ width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #c3a578; box-shadow: 0 2px 8px rgba(0,0,0,0.1); background: #e8ddd0; transition: transform 0.3s ease; }}
  .person img:hover {{ transform: scale(1.08); }}
  .fallback-avatar {{ width: 80px; height: 80px; border-radius: 50%; display: none; align-items: center; justify-content: center; font-size: 28px; color: #694128; font-weight: bold; background: #e8ddd0; }}
  .heart {{ font-size: 13px; color: #c47b8a; flex-shrink: 0; margin-top: -10px; }}
  .person-name {{ display: block; font-size: 11px; color: #372314; font-weight: bold; margin-top: 3px; line-height: 1.3; word-wrap: break-word; overflow-wrap: break-word; }}

  .kid-card {{ background: #fff; border-radius: 10px; padding: 10px 8px 8px; text-align: center; box-shadow: 0 2px 10px rgba(105,65,40,0.06); border: 2px solid #e8ddd0; flex-shrink: 0; }}
  .kid-card .person img {{ width: 60px; height: 60px; }}
  .kid-card .fallback-avatar {{ width: 60px; height: 60px; font-size: 22px; }}
  .kid-card .person-name {{ font-size: 10px; max-width: 58px; }}

  .children-hint {{ font-size: 10px; color: #a08060; margin-top: 4px; }}

  footer {{ text-align: center; padding: 36px 20px; color: #a08060; font-size: 13px; border-top: 1px solid #e8ddd0; margin-top: 16px; }}
  footer .ornament {{ font-size: 20px; color: #c3a578; margin-bottom: 8px; }}

  @media (max-width: 700px) {{
    .hero {{ padding: 8px 12px 6px; }}
    .hero h1 {{ font-size: 18px; letter-spacing: 1px; }}
    .root-card {{ padding: 8px 12px 6px; }}
    .root-card .person img, .root-card .fallback-avatar {{ width: 50px; height: 50px; font-size: 18px; }}
    .sibling-note {{ font-size: 11px; }}
    .branch-title {{ font-size: 18px; }}
    .branch-couple-card {{ padding: 12px 16px 10px; }}
    .branch-couple-card .person img, .branch-couple-card .fallback-avatar {{ width: 56px; height: 56px; font-size: 20px; }}
    .branch-couple-card .branch-sub {{ font-size: 11px; }}
    .siblings-scroll {{ padding: 0 16px; }}
    .siblings-row {{ gap: 10px; }}
    .family-card {{ padding: 10px 8px 8px; }}
    .family-card .person img, .family-card .fallback-avatar {{ width: 56px; height: 56px; font-size: 20px; }}
    .family-card .person-name {{ font-size: 10px; }}
    .kid-card {{ padding: 8px 6px 6px; }}
    .kid-card .person img, .kid-card .fallback-avatar {{ width: 44px; height: 44px; font-size: 16px; }}
    .kid-card .person-name {{ font-size: 9px; max-width: 50px; }}
    .kids-row {{ gap: 6px; }}
    .marriage-connector {{ padding: 12px 8px; }}
    .marriage-connector .connector-names {{ font-size: 12px; }}
    .marriage-connector .connector-label {{ font-size: 10px; }}
    footer {{ padding: 20px 12px; font-size: 11px; }}
  }}
</style>
</head>
<body>

<div class="hero">
  <h1>Family Tree</h1>
  <div class="root-card" style="margin-top:8px">
    <div class="couple-row">
      <div class="person"><img src="img/Roghaye.jpeg?v=1" alt="Roghaye" width="60" height="60" style="border-color:#c3a578" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div class="fallback-avatar" style="width:60px;height:60px;font-size:22px;border:3px solid #c3a578">R</div><span class="person-name" style="font-size:10px">Roghaye</span></div>
      <div class="heart" style="font-size:14px">&#10084;</div>
      <div class="person"><img src="img/Yousef.jpeg?v=1" alt="Yousef" width="60" height="60" style="border-color:#c3a578" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div class="fallback-avatar" style="width:60px;height:60px;font-size:22px;border:3px solid #c3a578">Y</div><span class="person-name" style="font-size:10px">Yousef</span></div>
    </div>
    <div class="sibling-note">Parents of Agha Hajbaba & Madarbozorg</div>
  </div>
  <div class="ornament" style="margin-top:6px">&#10022; &#10022; &#10022;</div>
  <div class="scroll-hint">Scroll left/right to see all family members</div>
</div>

<div id="tree-container"></div>

<footer>
  <div class="ornament">&#10087;</div>
  <div>Made with love for our family</div>
</footer>

<script>
const COLORS = {json.dumps(COLORS)};

const TREE = {tree_json};

function photoUrl(name, id) {{
  const fid = (id && id !== "1") ? ` ${{id}}` : "";
  return `img/${{encodeURIComponent(name + fid)}}.jpeg?v=${{Date.now()}}`;
}}
function initial(name) {{ return name.charAt(0).toUpperCase(); }}

const MALES = new Set(["Yousef","Agha_Hajbaba","Fattah","Amo_Yousef","Amo_Nasrollah","Amo_Fazi","Mehdi","Aghabozorg",
  "Amo_Khosro","Amo_Mirza","Behzad","Amo_Asghar","Day_Ali","Amo_Ayat","Day_Ahmad","Amo_Ali","Ramin",
  "Kurosch","Arsalan","Iman","Habib","Javad","Davoud","Sadegh","Ali","Mojtaba","Aria","Parsa","Parham",
  "Yasin","Barbod","Aryan","Barman","Soheil","Shahrouz","Mehrad","Mehrbod","Amir","Ashkan"]);
function getGender(name) {{ return MALES.has(name) ? "male" : "female"; }}

function hexToHSL(hex) {{
  let r = parseInt(hex.slice(1,3),16)/255, g = parseInt(hex.slice(3,5),16)/255, b = parseInt(hex.slice(5,7),16)/255;
  let max = Math.max(r,g,b), min = Math.min(r,g,b), h, s, l = (max+min)/2;
  if(max===min){{h=s=0}}else{{
    let d=max-min; s=l>0.5?d/(2-max-min):d/(max+min);
    if(max===r)h=((g-b)/d+(g<b?6:0))/6;else if(max===g)h=((b-r)/d+2)/6;else h=((r-g)/d+4)/6;
  }}
  return {{h:Math.round(h*360),s:Math.round(s*100),l:Math.round(l*100)}};
}}
function hslToHex(h,s,l){{s/=100;l/=100;let c=(1-Math.abs(2*l-1))*s,x=c*(1-Math.abs((h/60)%2-1)),m=l-c/2,r,g,b;if(h<60){{r=c;g=x;b=0}}else if(h<120){{r=x;g=c;b=0}}else if(h<180){{r=0;g=c;b=x}}else if(h<240){{r=0;g=x;b=c}}else if(h<300){{r=x;g=0;b=c}}else{{r=c;g=0;b=x}}r=Math.round((r+m)*255);g=Math.round((g+m)*255);b=Math.round((b+m)*255);return`#${{r.toString(16).padStart(2,"0")}}${{g.toString(16).padStart(2,"0")}}${{b.toString(16).padStart(2,"0")}}`}}
function shadeColor(hex,idx){{const hsl=hexToHSL(hex);const step=idx*12;const newL=Math.min(80,Math.max(30,hsl.l+step));return hslToHex(hsl.h,Math.max(25,hsl.s-idx*2),newL)}}

function personHTML(name, id, size, color) {{
  const px = size === "sm" ? 60 : 80;
  const fs = size === "sm" ? 22 : 28;
  const nfs = size === "sm" ? 11 : 12;
  const dn = name.replace(/_/g, " ");
  const url = photoUrl(name, id);
  const bc = color || "#c3a578";
  return `<div class="person"><img src="${{url}}" alt="${{dn}}" width="${{px}}" height="${{px}}" style="border-color:${{bc}}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div class="fallback-avatar" style="width:${{px}}px;height:${{px}}px;font-size:${{fs}}px;border:3px solid ${{bc}}">${{initial(name)}}</div><span class="person-name" style="font-size:${{nfs}}px">${{dn}}</span></div>`;
}}

function renderCouple(names, size, color) {{
  let h = '<div class="couple-row">';
  if (names.length === 3) {{
    const id1 = names[1];
    const id2 = names[2];
    const isId1 = /^\\d+$/.test(id1);
    const isId2 = /^\\d+$/.test(id2);
    if (isId1) {{
      h += personHTML(names[0], id1, size, color);
      h += '<div class="heart">&#10084;</div>';
      h += personHTML(names[2], "1", size, color);
    }} else if (isId2) {{
      h += personHTML(names[0], "1", size, color);
      h += '<div class="heart">&#10084;</div>';
      h += personHTML(names[1], id2, size, color);
    }} else {{
      h += personHTML(names[0], "1", size, color);
      h += '<div class="heart">&#10084;</div>';
      h += personHTML(names[1], "1", size, color);
    }}
  }} else if (names.length === 2) {{
    h += personHTML(names[0], "1", size, color);
    h += '<div class="heart">&#10084;</div>';
    h += personHTML(names[1], "1", size, color);
  }} else {{
    h += personHTML(names[0], "1", size, color);
  }}
  h += '</div>';
  return h;
}}

function buildChildSubtree(node, color) {{
  const hasC = node.c && node.c.length > 0;
  const hint = hasC
    ? `<div class="children-hint">${{node.c.length}} child${{node.c.length > 1 ? "ren" : ""}}</div>`
    : ``;

  let html = `<div class="child-subtree">`;
  html += `<div class="kid-card" style="border-left-color:${{color}}">${{renderCouple(node.p, "sm", color)}}${{hint}}</div>`;

  if (hasC) {{
    html += `<div class="vline-sm" style="background:${{color}}"></div>`;
    html += `<div class="kids-scroll"><div class="kids-row">`;
    node.c.forEach(child => {{
      html += buildChildSubtree(child, color);
    }});
    html += `</div></div>`;
  }}

  html += `</div>`;
  return html;
}}

function buildSiblingCol(node, baseColor) {{
  const hasC = node.c && node.c.length > 0;
  const hint = hasC
    ? `<div class="children-hint">${{node.c.length}} child${{node.c.length > 1 ? "ren" : ""}}</div>`
    : ``;

  let html = `<div class="sibling-col">`;
  html += `<div class="family-card" style="border-color:${{baseColor}}">${{renderCouple(node.p, null, baseColor)}}${{hint}}</div>`;

  if (hasC) {{
    html += `<div class="vline-sm" style="background:${{baseColor}}"></div>`;
    html += `<div class="kids-scroll"><div class="kids-row">`;
    node.c.forEach((child, i) => {{
      const childColor = shadeColor(baseColor, i);
      html += buildChildSubtree(child, childColor);
    }});
    html += `</div></div>`;
  }}

  html += `</div>`;
  return html;
}}

function render() {{
  const container = document.getElementById("tree-container");
  let html = "";

  TREE.branches.forEach((branch, bi) => {{
    html += `<div class="branch-section" data-branch="${{bi}}">
      <h2 class="branch-title" style="text-align:center">${{branch.title}}</h2>
      <div style="text-align:center"><div class="branch-couple-card">
        <div class="couple-row">${{personHTML(branch.main[0], "1")}}<div class="heart">&#10084;</div>${{personHTML(branch.main[1], "1")}}</div>
        <div class="branch-sub">${{branch.sub}}</div>
      </div></div>
      <div class="vline"></div>
      <div class="siblings-scroll"><div class="siblings-row">
        ${{branch.siblings.map((s, si) => buildSiblingCol(s, COLORS[si % COLORS.length])).join("")}}
      </div></div>
    </div>`;
    if (bi < TREE.branches.length - 1) {{
      if (TREE.crossBranchMarriages && TREE.crossBranchMarriages.length > 0) {{
        TREE.crossBranchMarriages.forEach(marriage => {{
          html += `<div class="marriage-connector">
            <div class="connector-line">
              <div class="connector-bar"></div>
              <div class="connector-icon">&#10084;</div>
              <div class="connector-bar"></div>
            </div>
            <div class="connector-names">${{marriage[0].replace(/_/g," ")}} & ${{marriage[1].replace(/_/g," ")}}</div>
            <div class="connector-label">Cousins married — connecting both families</div>
          </div>`;
        }});
      }}
    }}
  }});

  container.innerHTML = html;
  const obs = new IntersectionObserver(entries => {{ entries.forEach(e => {{ if (e.isIntersecting) e.target.classList.add("visible"); }}); }}, {{ threshold: 0.05 }});
  document.querySelectorAll(".branch-section").forEach(el => obs.observe(el));
}}

render();
</script>
</body>
</html>'''
    return html


def main():
    print(f"Reading {TREE_FILE}...")
    text = TREE_FILE.read_text()

    print("Parsing tree...")
    tree_data = build_tree(text)

    print("Generating HTML...")
    html = generate_html(tree_data)

    print(f"Writing {OUTPUT_FILE}...")
    OUTPUT_FILE.write_text(html)

    print("Done! Open site/index.html in a browser.")


if __name__ == "__main__":
    main()
