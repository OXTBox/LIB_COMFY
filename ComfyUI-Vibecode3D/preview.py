"""A still frame of an assembled game, drawn from the same numbers the script uses."""
import math

from PIL import Image, ImageDraw

W, H = 900, 600


def draw(g):
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    c = g["court"]
    ox, oy = W / 2, H / 2 + 10

    def P(x, y):
        return (ox + x, oy + y)

    def line(x1, y1, x2, y2, col, w=1):
        d.line([P(x1, y1), P(x2, y2)], fill=tuple(col), width=w)

    def ring(x, y, r, col, n=24):
        pts = [P(x + r * math.cos(i * 2 * math.pi / n), y + r * math.sin(i * 2 * math.pi / n)) for i in range(n + 1)]
        d.line(pts, fill=tuple(col), width=1)

    hw, hh, wall, goal = c["hw"], c["hh"], c["wall"], c["goal"]
    deco = tuple(int(v * 0.4) for v in wall)
    st, gr = c["style"], max(20, c["grid"])
    if st == "classic":
        for i in range(14):
            if g["axis"] == "x":
                line(0, -hh + (i + .25) * 2 * hh / 14, 0, -hh + (i + .75) * 2 * hh / 14, deco)
            else:
                line(-hw + (i + .25) * 2 * hw / 14, 0, -hw + (i + .75) * 2 * hw / 14, 0, deco)
        ring(0, 0, 40, deco, 20)
    elif st == "grid":
        x = 0
        while x < hw:
            line(x, -hh, x, hh, deco)
            line(-x, -hh, -x, hh, deco)
            x += gr
        y = 0
        while y < hh:
            line(-hw, y, hw, y, deco)
            line(-hw, -y, hw, -y, deco)
            y += gr
    elif st == "rings":
        r = gr
        while r < min(hw, hh):
            ring(0, 0, r, deco, 28)
            r += gr
    edges = {"T": (-hw, -hh, hw, -hh), "B": (-hw, hh, hw, hh), "L": (-hw, -hh, -hw, hh), "R": (hw, -hh, hw, hh)}
    for side, (x1, y1, x2, y2) in edges.items():
        line(x1, y1, x2, y2, goal if side in g["goals"] else wall, 2)
    for p in g["paddles"]:
        if p["side"] in ("L", "R"):
            box = [P(p["fx"] - 5, -p["half"]), P(p["fx"] + 5, p["half"])]
        else:
            box = [P(-p["half"], p["fx"] - 5), P(p["half"], p["fx"] + 5)]
        d.rectangle(box, outline=tuple(p["color"]), width=2)
    b = g["ball"]
    n = b["count"]
    for i in range(n):
        y = (i + 1 - (n + 1) / 2) * b["size"] * 3
        s = b["size"] / 2
        col = tuple(b["color"])
        if b["shape"] == "diamond":
            d.polygon([P(0, y - s - 2), P(s + 2, y), P(0, y + s + 2), P(-s - 2, y)], outline=col)
        elif b["shape"] == "ring":
            ring(0, y, s + 1, col, 10)
        else:
            d.rectangle([P(-s, y - s), P(s, y + s)], outline=col, width=2)
    d.text((20, 14), "%s   seed %s   %s" % (g["title"].upper(), g["seed"], g.get("file_name", "")), fill=tuple(wall))
    d.text((20, 32), "parts: " + ", ".join(g.get("parts", [])), fill=tuple(deco))
    for i, note in enumerate(g["notes"][:4]):
        d.text((20, H - 20 - 16 * i), note, fill=(255, 200, 80))
    return im
