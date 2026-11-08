"""Tiny vector toolkit: build outlines once, emit them as SVG and as
PowerPoint custom-geometry (DrawingML <a:custGeom>) so the deck holds real,
editable vector shapes instead of pictures.

A path is a list of subpaths; a subpath is a list of commands in page pixel
coordinates (source-scan pixels, y down):
    ("M", x, y) | ("L", x, y) | ("Q", x1, y1, x, y) | ("C", x1, y1, x2, y2, x, y) | ("Z",)
"""
import math
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen


# ---------------------------------------------------------------- geometry
def arc_cubics(cx, cy, r, a0, a1, segs=4):
    """Circular arc a0->a1 (radians, y-down screen coords) as cubic commands."""
    out = []
    step = (a1 - a0) / segs
    k = 4 / 3 * math.tan(step / 4)
    for i in range(segs):
        t0 = a0 + i * step
        t1 = t0 + step
        p0 = (cx + r * math.cos(t0), cy + r * math.sin(t0))
        p3 = (cx + r * math.cos(t1), cy + r * math.sin(t1))
        p1 = (p0[0] - k * r * math.sin(t0), p0[1] + k * r * math.cos(t0))
        p2 = (p3[0] + k * r * math.sin(t1), p3[1] - k * r * math.cos(t1))
        out.append(("C", p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]))
    return out


def transform(path, fn):
    """Apply point function fn(x, y)->(x, y) to every coordinate."""
    res = []
    for sp in path:
        nsp = []
        for c in sp:
            if c[0] == "Z":
                nsp.append(c)
                continue
            pts = [fn(c[i], c[i + 1]) for i in range(1, len(c), 2)]
            nsp.append((c[0],) + tuple(v for p in pts for v in p))
        res.append(nsp)
    return res


def bbox(path):
    xs, ys = [], []
    for sp in path:
        for c in sp:
            xs += list(c[1::2])
            ys += list(c[2::2])
    return min(xs), min(ys), max(xs), max(ys)


# ---------------------------------------------------------------- fonts -> paths
class _Pen(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.path, self.cur = [], None

    def _moveTo(self, p):
        self.cur = [("M",) + tuple(p)]
        self.path.append(self.cur)

    def _lineTo(self, p):
        self.cur.append(("L",) + tuple(p))

    def _qCurveToOne(self, p1, p2):
        self.cur.append(("Q",) + tuple(p1) + tuple(p2))

    def _curveToOne(self, p1, p2, p3):
        self.cur.append(("C",) + tuple(p1) + tuple(p2) + tuple(p3))

    def _closePath(self):
        self.cur.append(("Z",))

    _endPath = _closePath


class FontOutline:
    def __init__(self, path):
        self.font = TTFont(path)
        self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upem = self.font["head"].unitsPerEm
        self.hmtx = self.font["hmtx"]

    def glyphs(self, text, tracking=0):
        """Return [(char, path_in_font_units_y_up, x_offset)], advance."""
        x = 0
        out = []
        for ch in text:
            gn = self.cmap[ord(ch)]
            pen = _Pen(self.gs)
            self.gs[gn].draw(pen)
            if pen.path:
                out.append((ch, transform(pen.path, lambda a, b, x=x: (a + x, b)), x))
            x += self.hmtx[gn][0] + tracking
        return out, x - tracking


def fit_word(glyphs, box):
    """Scale the ink bbox of a list of glyph paths into box=(x0,y0,x1,y1) px (y down)."""
    allp = [sp for _, p, _ in glyphs for sp in p]
    gx0, gy0, gx1, gy1 = bbox(allp)
    x0, y0, x1, y1 = box
    sx = (x1 - x0) / (gx1 - gx0)
    sy = (y1 - y0) / (gy1 - gy0)
    fn = lambda a, b: (x0 + (a - gx0) * sx, y0 + (gy1 - b) * sy)
    return [(ch, transform(p, fn)) for ch, p, _ in glyphs]


# ---------------------------------------------------------------- SVG
def svg_d(path, nd=2):
    f = lambda v: f"{v:.{nd}f}".rstrip("0").rstrip(".")
    parts = []
    for sp in path:
        for c in sp:
            if c[0] == "Z":
                parts.append("Z")
            else:
                parts.append(c[0] + " ".join(f(v) for v in c[1:]))
    return "".join(parts)


# ---------------------------------------------------------------- DrawingML
def custgeom_xml(path, emu_per_px):
    """Return (x, y, cx, cy) in EMU and the <a:custGeom> xml for a path."""
    x0, y0, x1, y1 = bbox(path)
    w = max(x1 - x0, 1e-3)
    h = max(y1 - y0, 1e-3)
    W = max(int(round(w * emu_per_px)), 1)
    H = max(int(round(h * emu_per_px)), 1)
    pt = lambda x, y: (f'<a:pt x="{int(round((x - x0) * emu_per_px))}" '
                       f'y="{int(round((y - y0) * emu_per_px))}"/>')
    body = []
    for sp in path:
        for c in sp:
            t = c[0]
            if t == "M":
                body.append(f"<a:moveTo>{pt(c[1], c[2])}</a:moveTo>")
            elif t == "L":
                body.append(f"<a:lnTo>{pt(c[1], c[2])}</a:lnTo>")
            elif t == "Q":
                body.append(f"<a:quadBezTo>{pt(c[1], c[2])}{pt(c[3], c[4])}</a:quadBezTo>")
            elif t == "C":
                body.append(f"<a:cubicBezTo>{pt(c[1], c[2])}{pt(c[3], c[4])}{pt(c[5], c[6])}</a:cubicBezTo>")
            elif t == "Z":
                body.append("<a:close/>")
    xml = ('<a:custGeom xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
           '<a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
           '<a:rect l="0" t="0" r="r" b="b"/>'
           f'<a:pathLst><a:path w="{W}" h="{H}">{"".join(body)}</a:path></a:pathLst>'
           '</a:custGeom>')
    return (x0 * emu_per_px, y0 * emu_per_px, W, H), xml
