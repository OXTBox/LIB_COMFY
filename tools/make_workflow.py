"""Writes the starter workflow in both ComfyUI formats:
  workflows/vector_pong_variants.json      drag into ComfyUI (the editor format)
  workflows/vector_pong_variants_api.json  for queueing from a script (tools/queue.sh)
Each step: (type, widget values in order, the seed widget gets 'randomize' after it)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
CHAIN = [
    ("VC3D_GameStart", ["Comfy Pong", "ComfyPong", 1, 1.0], {"title": "Comfy Pong", "name": "ComfyPong", "seed": 1, "dice": 1.0}),
    ("VC3D_Palette", [190, "random", 0.5], {"hue": 190, "scheme": "random", "dice": 0.5}),
    ("VC3D_Court", [760, 420, "random", 60, "auto", "auto", 0.5],
     {"width": 760, "height": 420, "style": "random", "grid": 60, "wall_color": "auto", "goal_color": "auto", "dice": 0.5}),
    ("VC3D_Paddle", ["L", "arrows", "auto", 90, 9.0, 24, 0.6, "auto", 1.0, 0.5], None),
    ("VC3D_Paddle", ["R", "cpu", "auto", 90, 8.0, 24, 0.6, "auto", 1.0, 0.5], None),
    ("VC3D_Paddle", ["T", "cpu", "auto", 120, 8.0, 24, 0.6, "auto", 0.5, 0.5], None),
    ("VC3D_Paddle", ["R", "cpu", "auto", 60, 8.0, 220, 0.5, "auto", 0.4, 0.5], None),
    ("VC3D_Ball", [14, 7.0, 1.05, 16.0, 1, "random", "auto", 0.5], None),
    ("VC3D_MatchRules", [5, 3, 0.15, 0.5], None),
    ("VC3D_BuildGame", [True, "LIB_GAMES (the game launcher sees it)"], None),
]
PADDLE = ["side", "control", "team", "length", "speed", "inset", "skill", "color", "appear", "dice"]
NAMES = {"VC3D_Ball": ["size", "speed", "speed_up", "top_speed", "count", "shape", "color", "dice"],
         "VC3D_MatchRules": ["points_to_win", "levels", "level_speed_up", "dice"],
         "VC3D_BuildGame": ["add_seed_to_name", "save_to"], "VC3D_Paddle": PADDLE}
nodes, links, api = [], [], {}
x = 40
for i, (typ, vals, named) in enumerate(CHAIN, 1):
    widgets = list(vals)
    if typ == "VC3D_GameStart":
        widgets.insert(3, "randomize")
    inputs = [] if i == 1 else [{"name": "game", "type": "VC3D_GAME", "link": i - 1}]
    if typ == "VC3D_BuildGame":
        outputs = [{"name": "script_path", "type": "STRING", "links": None, "slot_index": 0},
                   {"name": "preview", "type": "IMAGE", "links": [len(CHAIN)], "slot_index": 1},
                   {"name": "script", "type": "STRING", "links": None, "slot_index": 2}]
    else:
        outputs = [{"name": "game", "type": "VC3D_GAME", "links": [i], "slot_index": 0}]
    col, row = (i - 1) % 5, (i - 1) // 5
    nodes.append({"id": i, "type": typ, "pos": [40 + col * 330, 60 + row * 420], "size": [300, 300],
                  "flags": {}, "order": i - 1, "mode": 0, "inputs": inputs, "outputs": outputs,
                  "properties": {"Node name for S&R": typ}, "widgets_values": widgets})
    if i > 1:
        links.append([i - 1, i - 1, 0, i, 0, "VC3D_GAME"])
    a = dict(named) if named else dict(zip(NAMES[typ], vals))
    if i > 1:
        a["game"] = [str(i - 1), 0]
    api[str(i)] = {"class_type": typ, "inputs": a}
pid = len(CHAIN) + 1
nodes.append({"id": pid, "type": "PreviewImage", "pos": [40 + 330 * 1, 60 + 420 * 2], "size": [600, 420],
              "flags": {}, "order": pid - 1, "mode": 0,
              "inputs": [{"name": "images", "type": "IMAGE", "link": len(CHAIN)}], "outputs": [],
              "properties": {"Node name for S&R": "PreviewImage"}, "widgets_values": []})
links.append([len(CHAIN), len(CHAIN), 1, pid, 0, "IMAGE"])
api[str(pid)] = {"class_type": "PreviewImage", "inputs": {"images": [str(len(CHAIN)), 1]}}
ui = {"last_node_id": pid, "last_link_id": len(CHAIN), "nodes": nodes, "links": links,
      "groups": [], "config": {}, "extra": {}, "version": 0.4}
out = os.path.join(HERE, "..", "workflows")
json.dump(ui, open(os.path.join(out, "vector_pong_variants.json"), "w"), indent=1)
json.dump(api, open(os.path.join(out, "vector_pong_variants_api.json"), "w"), indent=1)
print("wrote", len(nodes), "nodes,", len(links), "links")
