"""Build the Lu-Mi-Num carbide lamp ad as an editable 3:4 PowerPoint slide.

- Lamp illustrations: cut from the scan (lamps.py), placed as transparent PNG.
- Border: one primitive unit drawn as a vector path, repeated around the page,
  each repetition a native PowerPoint freeform (custom geometry).
- Logos: redrawn as vector outlines, one native freeform per letter.
- All copy: live text boxes set in Google Fonts.
- The same vectors are also written out as SVG source files.

Coordinates are source-scan pixels (1532 x 2042, i.e. 3:4); 1 px = EMU_PX EMU.
"""
import copy
import math
import os
import sys

from lxml import etree
from PIL import ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

import lamps
import vec

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
FONTDIR = os.environ.get("FONTDIR", os.path.expanduser("~/.fonts"))

SLIDE_W, SLIDE_H = 6858000, 9144000          # 7.5 x 10 in  (3:4)
PX_W, PX_H = 1532, 2042
EMU_PX = SLIDE_H / PX_H                       # ~4478 EMU per source pixel
PT_PX = EMU_PX / 12700                        # points per source pixel (~0.3526)
INK = RGBColor(0x1A, 0x1A, 0x1A)

# Google Fonts used (family name as PowerPoint sees it -> local file for metrics)
FONTS = {
    ("Cormorant SC", True): "CormorantSC-Bold.ttf",
    ("Libre Caslon Text", False): "LibreCaslonText-Regular.ttf",
    ("Libre Caslon Text", True): "LibreCaslonText-Bold.ttf",
    ("Courier Prime", False): "CourierPrime-Regular.ttf",
    ("Courier Prime", True): "CourierPrime-Bold.ttf",
    ("Archivo Black", False): "ArchivoBlack-Regular.ttf",
    ("Old Standard TT", False): "OldStandard-Regular.ttf",
    ("Old Standard TT", True): "OldStandard-Bold.ttf",
}
HEAD = "Cormorant SC"
SERIF = "Libre Caslon Text"
TYPE = "Old Standard TT"
MONO = "Courier Prime"
GOTHIC = "Archivo Black"

# baseline offset of first line inside a box with exact line spacing,
# as a fraction of the line pitch (calibrated against the rendered slide)
BASE_FRAC = 0.80


def E(px):
    return Emu(int(round(px * EMU_PX)))


_fcache = {}


def pil_font(family, bold, size_px):
    key = (family, bold, round(size_px * 4))
    if key not in _fcache:
        _fcache[key] = ImageFont.truetype(os.path.join(FONTDIR, FONTS[(family, bold)]),
                                          max(1, int(round(size_px * 4))))
    return _fcache[key]


def text_w(s, family, bold, size_px, spc_px=0.0):
    """Advance width of s in px at size_px (measured at 4x for precision)."""
    return pil_font(family, bold, size_px).getlength(s) / 4 + spc_px * len(s)


# ============================================================ text helpers
def _style_run(run, family, bold, size_px, spc_px=0.0, italic=False):
    f = run.font
    f.name = family
    f.size = Pt(round(size_px * PT_PX * 2) / 2)
    f.bold = bold
    f.italic = italic
    f.color.rgb = INK
    rPr = run._r.get_or_add_rPr()
    if spc_px:
        rPr.set("spc", str(int(round(spc_px * PT_PX * 100))))
    # make sure every script slot uses the same face
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", family)


def textbox(slide, x0, x1, base1, pitch, paras, align="l", name=None, anchor_extra=0):
    """paras: list of paragraphs; each paragraph is a list of runs
    (text, family, bold, size_px[, spc_px]) or a dict with 'runs' and options
    ('indent' px first-line indent). Line pitch in px, first baseline at base1."""
    nlines = sum(p.get("lines", 1) if isinstance(p, dict) else 1 for p in paras)
    top = base1 - BASE_FRAC * pitch
    h = pitch * nlines + anchor_extra
    tb = slide.shapes.add_textbox(E(x0), E(top), E(x1 - x0), E(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.TOP
    al = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT, "j": PP_ALIGN.JUSTIFY}[align]
    for i, p in enumerate(paras):
        opts = p if isinstance(p, dict) else {"runs": p}
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = opts.get("align", al)
        para.line_spacing = Pt(round(pitch * PT_PX * 10) / 10)
        para.space_before = Pt(0)
        para.space_after = Pt(0)
        pPr = para._p.get_or_add_pPr()
        if opts.get("indent"):
            pPr.set("indent", str(int(round(opts["indent"] * EMU_PX))))
        if opts.get("just_last"):
            pass
        for r in opts["runs"]:
            run = para.add_run()
            run.text = r[0]
            _style_run(run, r[1], r[2], r[3], r[4] if len(r) > 4 else 0.0)
    return tb


def line(slide, x0, x1, base, text, family, bold, size_px, align="l", spc_px=0.0, name=None):
    pitch = size_px * 1.2
    return textbox(slide, x0, x1, base, pitch, [[(text, family, bold, size_px, spc_px)]], align, name)


def fit_size(text, family, bold, width_px):
    """Font size (px) at which text is exactly width_px wide."""
    return width_px / text_w(text, family, bold, 1000) * 1000


def fit_spc(text, family, bold, size_px, width_px):
    """Letter spacing (px) needed to stretch text to width_px."""
    n = max(len(text) - 1, 1)
    return (width_px - text_w(text, family, bold, size_px)) / n


def wrap_count(words, family, size_px, width, spc=0.0):
    lines, cur = 1, 0.0
    sp = text_w(" ", family, False, size_px, spc)
    for w in words:
        ww = text_w(w, family, False, size_px, spc)
        if cur and cur + sp + ww > width:
            lines += 1
            cur = ww
        else:
            cur = cur + sp + ww if cur else ww
    return lines


def fit_para(text, family, width, nlines, lo=5, hi=40, first_indent=0.0):
    """Largest size (px) at which text wraps into <= nlines lines of width."""
    words = text.split()
    best = lo
    s = lo
    while s <= hi:
        if wrap_count(words, family, s, width - 0.4) <= nlines:
            best = s
        s += 0.05
    return best


def fit_para_spc(text, family, size_px, width, nlines):
    """Largest letter spacing (px) at which text still wraps into nlines."""
    words = text.split()
    best = -0.6
    v = -0.6
    while v <= 3.0:
        if wrap_count(words, family, size_px, width * 0.975, v) <= nlines:
            best = v
        v += 0.02
    return best


def list_spc(rows, family, size_px, width):
    """Letter spacing so the longest (bold head + regular rest) row is width px."""
    best = None
    for h, r in rows:
        w0 = text_w(h, family, True, size_px) + text_w(r, family, False, size_px)
        n = len(h) + len(r)
        v = (width - w0) / n
        best = v if best is None else min(best, v)
    return best


def leader(label, family, bold, size_px, x0, x_end):
    """label followed by a dot leader reaching x_end."""
    base = text_w(label + " ", family, bold, size_px)
    dot = text_w(".", family, False, size_px)
    n = max(int((x_end - x0 - base) / dot), 3)
    return label + " " + "." * n


# ============================================================ vector parts
def border_unit(P):
    """One repeat of the beaded rule, top orientation, origin = top-left.
    Band 4.5 px with a hanging bead and two small spurs."""
    c = P / 2
    band = 4.6
    r, cy = 3.5, 6.1
    dx = math.sqrt(r * r - (cy - band) ** 2)
    a0 = math.atan2(band - cy, dx)               # just right of top of bead
    a1 = math.pi - a0
    sp = [("M", 0, 0), ("L", P, 0), ("L", P, band),
          ("L", c + 9.6, band), ("L", c + 8.0, band + 2.4), ("L", c + 6.4, band),
          ("L", c + dx, band)]
    sp += vec.arc_cubics(c, cy, r, a0, a1, segs=4)
    sp += [("L", c - 6.4, band), ("L", c - 8.0, band + 2.4), ("L", c - 9.6, band),
           ("L", 0, band), ("Z",)]
    return [sp]


FRAME = dict(outer=50.0, band=57.0)           # insets (px) of outer rule / band edge


def border_layout():
    """Yield (side, x, y, P, rot) for every unit (x,y = top-left of the
    unrotated unit box)."""
    L = R = None
    b = FRAME["band"]
    w = PX_W - 2 * b
    h = PX_H - 2 * b
    nh = round(w / 31.5)
    nv = round(h / 31.5)
    Ph, Pv = w / nh, h / nv
    hu = vec.bbox(border_unit(Ph))[3]
    out = []
    for i in range(nh):
        out.append(("top", b + i * Ph, b, Ph, 0))
        out.append(("bottom", b + i * Ph, PX_H - b - hu, Ph, 180))
    hv = vec.bbox(border_unit(Pv))[3]
    for i in range(nv):
        cy = b + i * Pv + Pv / 2
        # rotated boxes: unrotated box is Pv wide x hv tall, centred on the visual centre
        out.append(("left", b + hv / 2 - Pv / 2, cy - hv / 2, Pv, 270))
        out.append(("right", PX_W - b - hv / 2 - Pv / 2, cy - hv / 2, Pv, 90))
    return out, (Ph, Pv)


def logo_paths(ox=0.0):
    """Lu-Mi-Num trade mark, redrawn: returns [(label, path)] in page px."""
    hw = vec.FontOutline(os.path.join(FONTDIR, "HoltwoodOneSC-Regular.ttf"))
    cs = vec.FontOutline(os.path.join(FONTDIR, "LibreCaslonText-Bold.ttf"))
    parts = []

    def word(fo, text, box, tracking=0):
        g, _ = fo.glyphs(text, tracking)
        bx = (box[0] + ox, box[1], box[2] + ox, box[3])
        return vec.fit_word(g, bx)

    # the big initial L is drawn by hand (Clarendon-style slab with upturned foot)
    L = [[("M", 135, 131), ("L", 163, 131), ("L", 163, 134.6), ("Q", 157.8, 135, 157.4, 137.6),
          ("L", 157.4, 156.2), ("L", 178, 156.2), ("Q", 184.2, 155.6, 186, 149.6), ("L", 190.2, 149.6),
          ("L", 190.2, 163.6), ("L", 135, 163.6), ("L", 135, 160.2), ("Q", 140.4, 159.8, 140.8, 157.2),
          ("L", 140.8, 137.6), ("Q", 140.4, 135, 135, 134.6), ("Z",)]]
    parts.append(("L", vec.transform(L, lambda a, b: (a + ox, b))))
    parts += word(hw, "U-MI-NUM", (162, 131, 330, 145.5), tracking=20)
    for ch, box in (("A", (207, 149, 228, 162.5)), ("M", (251, 149, 281, 162.5)),
                    ("P", (300, 149, 328, 162.5))):
        parts += word(hw, ch, box)
    parts += word(cs, "TRADE", (207, 125, 253, 129.8), tracking=420)
    parts += word(cs, "MARK", (210, 165.5, 252, 170.3), tracking=420)
    return parts


# ============================================================ SVG sources
def write_svgs(Ph, Pv):
    d = os.path.join(BUILD, "svg")
    os.makedirs(d, exist_ok=True)
    u = border_unit(31.5)
    x0, y0, x1, y1 = vec.bbox(u)
    with open(os.path.join(d, "border_unit.svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {x1:.2f} {y1:.2f}" '
                f'width="{x1 * 4:.0f}" height="{y1 * 4:.0f}">\n'
                f'  <!-- one repeat of the beaded border rule (top orientation) -->\n'
                f'  <path d="{vec.svg_d(u)}" fill="#1a1a1a"/>\n</svg>\n')
    units, _ = border_layout()
    uses = []
    defs = (f'<path id="uh" d="{vec.svg_d(border_unit(Ph))}"/>'
            f'<path id="uv" d="{vec.svg_d(border_unit(Pv))}"/>')
    for side, x, y, P, rot in units:
        ref = "#uh" if side in ("top", "bottom") else "#uv"
        hu = vec.bbox(border_unit(P))[3]
        cx, cy = x + P / 2, y + hu / 2
        tr = f"translate({x:.2f} {y:.2f})"
        if rot:
            tr = f"rotate({rot} {cx:.2f} {cy:.2f}) " + tr
        uses.append(f'<use href="{ref}" transform="{tr}"/>')
    o = FRAME["outer"]
    with open(os.path.join(d, "border_frame.svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {PX_W} {PX_H}" '
                f'width="7.5in" height="10in">\n<defs>{defs}</defs>\n'
                f'<rect x="{o}" y="{o}" width="{PX_W - 2 * o}" height="{PX_H - 2 * o}" '
                f'fill="none" stroke="#1a1a1a" stroke-width="1.6"/>\n'
                f'<g fill="#1a1a1a">\n' + "\n".join(uses) + "\n</g>\n</svg>\n")
    parts = logo_paths()
    allp = [sp for _, p in parts for sp in p]
    x0, y0, x1, y1 = vec.bbox(allp)
    pad = 2
    with open(os.path.join(d, "logo_luminum.svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="{x0 - pad:.2f} {y0 - pad:.2f} {x1 - x0 + 2 * pad:.2f} {y1 - y0 + 2 * pad:.2f}" '
                f'width="{(x1 - x0 + 2 * pad) * 8:.0f}" height="{(y1 - y0 + 2 * pad) * 8:.0f}">\n'
                f'<g fill="#1a1a1a">\n')
        for ch, p in parts:
            f.write(f'  <path data-glyph="{ch}" d="{vec.svg_d(p, 3)}"/>\n')
        f.write("</g>\n</svg>\n")


# ============================================================ pptx vector shapes
def add_vec(shapes, path, name, rot=0, place=None):
    """Add a filled freeform for path. place=(x,y) overrides the top-left (px)."""
    (x, y, W, H), xml = vec.custgeom_xml(path, EMU_PX)
    if place is not None:
        x, y = place[0] * EMU_PX, place[1] * EMU_PX
    sh = shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(int(round(x))), Emu(int(round(y))), Emu(W), Emu(H))
    sh.name = name
    spPr = sh._element.spPr
    prst = spPr.find(qn("a:prstGeom"))
    prst.addprevious(etree.fromstring(xml))
    spPr.remove(prst)
    sh.fill.solid()
    sh.fill.fore_color.rgb = INK
    sh.line.fill.background()
    st = sh._element.find(qn("p:style"))
    if st is not None:
        sh._element.remove(st)
    if rot:
        sh.rotation = rot
    return sh


def build_border(slide):
    units, (Ph, Pv) = border_layout()
    o = FRAME["outer"]
    rect = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, E(o), E(o), E(PX_W - 2 * o), E(PX_H - 2 * o))
    rect.name = "Border outer rule"
    rect.fill.background()
    rect.line.color.rgb = INK
    rect.line.width = Emu(int(1.6 * EMU_PX))
    st = rect._element.find(qn("p:style"))
    if st is not None:
        rect._element.remove(st)
    for side in ("top", "right", "bottom", "left"):
        grp = slide.shapes.add_group_shape()
        grp.name = f"Border {side}"
        k = 0
        for s, x, y, P, rot in units:
            if s != side:
                continue
            k += 1
            add_vec(grp.shapes, border_unit(P), f"Border unit {side} {k}", rot=rot, place=(x, y))
    return Ph, Pv


def build_logo(slide, ox, name):
    grp = slide.shapes.add_group_shape()
    grp.name = name
    for i, (ch, p) in enumerate(logo_paths(ox)):
        add_vec(grp.shapes, p, f"{name} {ch} {i + 1}")


# ============================================================ copy
def build_text(slide):
    S = slide

    # ---- masthead
    sz = fit_size("Aluminum", HEAD, True, 945 - 580)
    line(S, 380, 1150, 170, "Aluminum", HEAD, True, sz, "c", name="Title 1")
    sz = fit_size("Miners Carbide Lamps", HEAD, True, 1200 - 330)
    line(S, 250, 1280, 254, "Miners Carbide Lamps", HEAD, True, sz, "c", name="Title 2")
    sz = fit_size("EQUIPPED WITH LOCKING DEVICE", SERIF, True, 1110 - 415)
    line(S, 300, 1230, 304, "EQUIPPED WITH LOCKING DEVICE", SERIF, True, sz, "c", name="Subtitle")
    sz = fit_size("FEATURES", SERIF, False, 283 - 132)
    textbox(S, 112, 302, 340, 27, [[("NEW", SERIF, False, sz)], [("FEATURES", SERIF, False, sz)]], "c",
            name="New features")
    textbox(S, 1248, 1428, 340, 27, [[("LIGHT", SERIF, False, sz)], [("WEIGHT", SERIF, False, sz)]], "c",
            name="Light weight")
    t = "The Greatest Improvement Ever Made On Any Miners Lamp"
    sz2 = 30.0
    line(S, 300, 1250, 362, t, SERIF, False, sz2, "c",
         spc_px=fit_spc(t, SERIF, False, sz2, 1225 - 327), name="Tagline")

    # ---- lamp captions
    for t, x0, x1 in (("WITH FLAT HOOK", 200, 415), ("WITH ROUND HOOK", 620, 865),
                      ("WITH FIBRE HANDLE", 1075, 1325)):
        s = 19.5
        line(S, x0 - 40, x1 + 40, 425, t, SERIF, False, s, "c",
             spc_px=fit_spc(t, SERIF, False, s, x1 - x0), name=f"Caption {t.title()}")
    g = 36.0
    textbox(S, 120, 230, 736, 33, [[("No.", GOTHIC, False, g)], [("4-F", GOTHIC, False, g)]], "l", name="No. 4-F")
    textbox(S, 572, 680, 714, 32, [[("No.", GOTHIC, False, g)], [(" 4", GOTHIC, False, g)]], "l", name="No. 4")
    textbox(S, 1300, 1398, 741, 33, [[("No.", GOTHIC, False, g)], [("4-H", GOTHIC, False, g)]], "r", name="No. 4-H")
    tp = 15.6
    textbox(S, 857, 1060, 742, 16, [[("Patented", MONO, False, tp)], [("Feb. 5, 1924", MONO, False, tp)],
                                    [("Dec. 28, 1926", MONO, False, tp)], [(" Others Pending", MONO, False, tp)]],
            "l", name="Patents")
    for t, x0, x1 in (("Used on Water-Proof Hats", 160, 440), ("Used on Regular Miners Cap", 585, 890)):
        s = fit_size(t, SERIF, True, x1 - x0)
        line(S, x0 - 30, x1 + 30, 843, t, SERIF, True, s, "c", name=t)

    # ---- price block (left)
    line(S, 380, 610, 890, "PRICE", SERIF, False, fit_size("PRICE", SERIF, False, 100), "c", name="Price head")
    textbox(S, 780, 935, 889, 16, [[("West of", MONO, False, 15.6)], [("Denver and", MONO, False, 15.6)],
                                   [("Canada", MONO, False, 15.6)]], "c", name="West of Denver")
    t1, t2 = "No. 4 and No. 4-F Lamp", " with"
    s = fit_size(t1 + t2, SERIF, True, 597 - 222)
    line(S, 200, 640, 932, "", SERIF, True, s, "l", name="Price lamp head")
    tb = S.shapes[-1]
    p = tb.text_frame.paragraphs[0]
    for r in list(p.runs):
        p._p.remove(r._r)
    for txt, b in ((t1, True), (t2, False)):
        rr = p.add_run()
        rr.text = txt
        _style_run(rr, SERIF, b, s)
    tb.left = E(222)
    ps = 25.5
    rows = ((958, "2¼\"", "Aluminum Reflector", "$1.85", "$2.00"),
            (985, "3\"", "Brass N. P. Reflector", "2.00", "2.15"))
    for base, size_, label, p1, p2 in rows:
        line(S, 128, 205, base, size_, SERIF, False, ps, "l", name=f"Price size {size_}")
        line(S, 210, 700, base, leader(label, SERIF, False, ps, 210, 690), SERIF, False, ps, "l",
             name=f"Price row {label}")
        line(S, 660, 756, base, p1, SERIF, True, ps, "r", name=f"Price {p1}")
        line(S, 790, 890, base, p2, SERIF, True, ps, "r", name=f"Price west {p2}")

    # ---- improved reflector
    s = 18.5
    textbox(S, 200, 460, 1016, 20, [[("IMPROVED", SERIF, True, s)], [("3-inch Reflector", SERIF, True, s)]], "c",
            name="Improved reflector head")
    para = ("New design—concentrates and projects a strong spot light. Shows the bad roof clearly and "
            "gives a bright clean light for close by work. Extra heavy plate, can be cleaned and kept bright "
            "with a few drops of ammonia. The new design makes it especially strong and increases the "
            "lighting value.")
    s = 19.0
    v = fit_para_spc(para, TYPE, s, 510 - 132, 9)
    textbox(S, 132, 510, 1055, 16.7, [{"runs": [(para, TYPE, False, s, v)]}], "j", name="Improved reflector text")

    # ---- repair kit box
    bx = S.shapes.add_shape(MSO_SHAPE.RECTANGLE, E(527), E(1011), E(1003 - 527), E(1185 - 1011))
    bx.name = "Repair kit box"
    bx.fill.background()
    bx.line.color.rgb = INK
    bx.line.width = Emu(int(2.2 * EMU_PX))
    st = bx._element.find(qn("p:style"))
    if st is not None:
        bx._element.remove(st)
    t = "REPAIR KIT FREE WITH EACH LAMP"
    line(S, 535, 995, 1056, t, SERIF, True, fit_size(t, SERIF, True, 985 - 543), "c", name="Repair kit head")
    line(S, 600, 930, 1083, "Including", TYPE, False, 15.6, "c", name="Repair kit including")
    ks = 17.5
    items_l = (("2 Gaskets", "$0.10"), ("1 Lava Tip", ".05"), ("1 Hook", ".05"))
    items_r = (("1 Cleaning Tool", "$0.10"), ("1 Locking Clamp", ".05"), ("1 Cap Clasp", ".25"))
    for i, ((a, pa), (b, pb)) in enumerate(zip(items_l, items_r)):
        base = 1106 + i * 17
        wa = text_w(pa, TYPE, True, ks)
        line(S, 543, 780 - wa, base, leader(a, TYPE, False, ks, 543, 780 - wa - 4), TYPE, False, ks, "l",
             name=f"Kit {a}")
        line(S, 700, 780, base, pa, TYPE, True, ks, "r", name=f"Kit {a} price")
        wb = text_w(pb, TYPE, True, ks)
        lab = b if len(b) > 12 else leader(b, TYPE, False, ks, 787, 985 - wb - 4)
        line(S, 787, 985 - wb, base, lab, TYPE, False, ks, "l", name=f"Kit {b}")
        line(S, 900, 986, base, pb, TYPE, True, ks, "r", name=f"Kit {b} price")
    line(S, 600, 930, 1162, "Value 60 Cents", TYPE, False, ks, "c", name="Repair kit value")

    # ---- right column: small lamp for superintendents
    rs = 23.0
    for base, size_, label, pr in ((880, "2¼\"", "Aluminum Reflector", "$2.15"),
                                   (902, "3\"", "Brass N. P. Reflector", "2.25")):
        wpr = text_w(pr, SERIF, True, rs)
        txt = size_ + " " + label
        line(S, 990, 1400 - wpr, base, leader(txt, SERIF, False, rs, 990, 1400 - wpr - 3), SERIF, False, rs, "l",
             name=f"Small lamp {size_}")
        line(S, 1300, 1401, base, pr, SERIF, True, rs, "r", name=f"Small lamp price {pr}")
    textbox(S, 980, 1412, 925, 19.5, [[("For Superintendents, Engineers, Etc.", MONO, False, 17.2, 0.9)],
                                      [("Also Used as a Camp Lamp", MONO, False, 17.2, 0.9)]], "c",
            name="Superintendents")
    t = "SPECIFICATIONS: SMALL LAMPS"
    line(S, 1010, 1412, 970, t, SERIF, True, fit_size(t, SERIF, True, 1400 - 1022), "c", name="Spec small head")
    specs = (("Construction", "—Die-Cast, Seamless."), ("Material", "—Aluminum."),
             ("Height", "—3½ inches."), ("Diameter Cup", "—2″, rim 3/16″ thick."),
             ("Weight", "—6¼ ounces."), ("Reflector", "—Aluminum, 2¼″ diameter."),
             ("Capacity", "—2 hours, charge 1½ ozs."),
             ("Walls", "—1/16″ thick, exclusive of ribs."))
    ss = 19.5
    v = list_spc(specs, TYPE, ss, 1400 - 1022)
    textbox(S, 1022, 1412, 995, 22.15, [[(h, TYPE, True, ss, v), (r, TYPE, False, ss, v)] for h, r in specs], "l",
            name="Spec small list")

    # ---- separator
    ln = S.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(100), E(1197), E(1006), E(1197))
    ln.name = "Section rule"
    ln.line.color.rgb = INK
    ln.line.width = Emu(int(1.6 * EMU_PX))
    st = ln._element.find(qn("p:style"))
    if st is not None:
        ln._element.remove(st)

    # ---- large lamp copy
    t = "Large Size Lu-mi-num Lamp"
    line(S, 110, 760, 1258, t, SERIF, True, fit_size(t, SERIF, True, 733 - 132), "c", name="Large lamp head")
    t = "WITH PATENTED LOCKING DEVICE"
    s = 21.0
    line(S, 150, 720, 1288, t, SERIF, True, s, "c", spc_px=fit_spc(t, SERIF, True, s, 650 - 220),
         name="Large lamp subhead")
    p1 = ("*New AUTOMATIC DROP WATER FEED with self-cleaning valve. The water drop is controlled by a coiled "
          "spring made of non-corrosive Monel wire inside of water tube. The prongs on the valve seat rotate "
          "with the Lever and prevent the carbide sludge from clogging the water outlet. The uniform water "
          "drop and self-cleaning valve insures a steady flame, prevents over-generation and SAVES carbide. "
          "This improved generator would be desirable in any kind of a lamp, brass or steel, but, in the "
          "strong, seamless die-cast Lu-Mi-Num lamp it makes a perfect mine light, combining great strength, "
          "durability, economy and dependability. It is, in fact, the first real FOOL-PROOF miners lamp made.")
    p2 = ("If a hand regulated water feed is preferred it can be easily changed by removing the coiled wire "
          "from the valve stem.")
    w = 735 - 130
    s = 18.0
    v = fit_para_spc(p1, SERIF, s, w, 13)
    textbox(S, 130, 735, 1307, 21.5,
            [{"runs": [(p1, SERIF, False, s, v)], "lines": 13},
             {"runs": [("*Note", SERIF, True, s, v), ("—" + p2, SERIF, False, s, v)], "indent": 20,
              "lines": 3}],
            "j", name="Large lamp text")
    line(S, 230, 630, 1651, "SPECIFICATIONS", SERIF, True, fit_size("SPECIFICATIONS", SERIF, True, 525 - 332),
         "c", name="Spec large head")
    specs = (("Construction", "—Aluminum, cast in steel dies."), ("Height", "—5¾ inches, exclusive of bail."),
             ("Dia. Cup", "—3 inches, bottom edge ¼ inch thick."),
             ("Reflector", "—Brass, see description above."), ("Weight", "—26 ounces."),
             ("Bail and Hook", "—Rust-Proofed steel."),
             ("Handle", "—Detachable, fits in slot, rust-proof."),
             ("Bail Screw", "—Specially designed, will not work loose."),
             ("Metal", " is 3/32″ thick, exclusive of the ribs."),
             ("Locking Device", "—See description on opposite page."))
    v = list_spc(specs, TYPE, 17.5, 630 - 130)
    textbox(S, 130, 735, 1669, 16.67, [[(h, TYPE, True, 17.5, v), (r, TYPE, False, 17.5, v)] for h, r in specs], "l",
            name="Spec large list")
    line(S, 230, 630, 1840, "DURABILITY", SERIF, True, fit_size("DURABILITY", SERIF, True, 500 - 359), "c",
         name="Durability head")
    pd = ("It is the only miner’s lamp that can be taken completely apart for cleaning or repairing and "
          "every part of the lamp can be replaced. The two shells, Water Tank and Carbide Cup are practically "
          "indestructible and with reasonable care the Lu-Mi-Num lamp will last indefinitely.")
    s = 18.0
    v = fit_para_spc(pd, TYPE, s, 733 - 128, 4)
    textbox(S, 128, 733, 1856, 16.7, [{"runs": [(pd, TYPE, False, s, v)]}], "j", name="Durability text")

    # ---- large lamp side notes
    textbox(S, 1195, 1420, 1667, 25, [[("Burning Capacity", SERIF, False, 20.5)],
                                      [("5 to 6 Hours", SERIF, False, 20.5)]], "c", name="Burning capacity")
    pn = "For detail description and new features, see opposite page. For Repair Parts, see last page"
    s = 17.5
    v = min(fit_para_spc(pn, TYPE, s, 1405 - 1210, 5), 0.8)
    textbox(S, 1210, 1410, 1777, 16.3, [{"runs": [(pn, TYPE, False, s, v)]}], "l", name="Detail note")
    t = "No. 7 — Price, $4.25"
    line(S, 840, 1160, 1893, t, SERIF, True, fit_size(t, SERIF, True, 1110 - 885), "c", name="No. 7 price")


# ============================================================ main
def main():
    os.makedirs(BUILD, exist_ok=True)
    boxes = lamps.main()
    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    Ph, Pv = build_border(slide)
    build_logo(slide, 0, "Logo left")
    build_logo(slide, 1065, "Logo right")
    for name, (x0, y0, x1, y1) in boxes.items():
        pic = slide.shapes.add_picture(os.path.join(BUILD, "img", name + ".png"), E(x0), E(y0),
                                       E(x1 - x0), E(y1 - y0))
        pic.name = {"lamp_4F": "Lamp No. 4-F", "lamp_4": "Lamp No. 4", "lamp_4H": "Lamp No. 4-H",
                    "lamp_7": "Lamp No. 7"}[name]
    build_text(slide)
    write_svgs(Ph, Pv)
    out = os.path.join(BUILD, "LuMiNum_CarbideLamps.pptx")
    prs.save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
