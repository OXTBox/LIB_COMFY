"""Writes one starter workflow per genre kit, in both ComfyUI formats, from tools/kit_chains.py:
  workflows/<kit>_variants.json       drag into ComfyUI (the editor format)
  workflows/<kit>_variants_api.json   for queueing from a script (POST /prompt)
Widget order comes from each node's INPUT_TYPES, so the files follow the nodes as they are.
    python3 -I tools/make_kit_workflows.py"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tests"))
import kit_chains  # noqa: E402
import kit_test  # noqa: E402

BUILD = ("VC3D_BuildGame", {"add_seed_to_name": True, "save_to": "LIB_GAMES (the game launcher sees it)"})


def widgets(cls, values):
    """widget values in the node's input order; a seed gets its 'control after generate' value after it"""
    out = []
    for name, spec in cls.INPUT_TYPES()["required"].items():
        if name == "game":
            continue
        out.append(values[name])
        if len(spec) > 1 and isinstance(spec[1], dict) and spec[1].get("control_after_generate"):
            out.append("randomize")
    return out


def write(kit, vc, out_dir):
    steps = kit_chains.chain(kit) + [BUILD]
    nodes, links, api = [], [], {}
    per_row = 5
    for i, (key, values) in enumerate(steps, 1):
        cls = vc.NODE_CLASS_MAPPINGS[key]
        inputs = [] if i == 1 else [{"name": "game", "type": "VC3D_GAME", "link": i - 1}]
        if key == "VC3D_BuildGame":
            outputs = [{"name": "script_path", "type": "STRING", "links": None, "slot_index": 0},
                       {"name": "preview", "type": "IMAGE", "links": [len(steps)], "slot_index": 1},
                       {"name": "script", "type": "STRING", "links": None, "slot_index": 2}]
        else:
            outputs = [{"name": "game", "type": "VC3D_GAME", "links": [i], "slot_index": 0}]
        col, row = (i - 1) % per_row, (i - 1) // per_row
        nodes.append({"id": i, "type": key, "pos": [40 + col * 330, 60 + row * 440], "size": [300, 320],
                      "flags": {}, "order": i - 1, "mode": 0, "inputs": inputs, "outputs": outputs,
                      "properties": {"Node name for S&R": key}, "widgets_values": widgets(cls, values)})
        if i > 1:
            links.append([i - 1, i - 1, 0, i, 0, "VC3D_GAME"])
        a = dict(values)
        if i > 1:
            a["game"] = [str(i - 1), 0]
        api[str(i)] = {"class_type": key, "inputs": a}
    pid = len(steps) + 1
    rows = (len(steps) - 1) // per_row + 1
    nodes.append({"id": pid, "type": "PreviewImage", "pos": [40 + 330, 60 + 440 * rows], "size": [620, 440],
                  "flags": {}, "order": pid - 1, "mode": 0,
                  "inputs": [{"name": "images", "type": "IMAGE", "link": len(steps)}], "outputs": [],
                  "properties": {"Node name for S&R": "PreviewImage"}, "widgets_values": []})
    links.append([len(steps), len(steps), 1, pid, 0, "IMAGE"])
    api[str(pid)] = {"class_type": "PreviewImage", "inputs": {"images": [str(len(steps)), 1]}}
    ui = {"last_node_id": pid, "last_link_id": len(steps), "nodes": nodes, "links": links,
          "groups": [], "config": {}, "extra": {}, "version": 0.4}
    with open(os.path.join(out_dir, "%s_variants.json" % kit), "w") as f:
        json.dump(ui, f, indent=1)
    with open(os.path.join(out_dir, "%s_variants_api.json" % kit), "w") as f:
        json.dump(api, f, indent=1)
    return len(nodes), len(links)


def main():
    vc = kit_test.load_pack()
    out_dir = os.path.join(HERE, "..", "workflows")
    for kit in kit_chains.KITS:
        n, l = write(kit, vc, out_dir)
        print("%s: %d nodes, %d links" % (kit, n, l))


if __name__ == "__main__":
    main()
