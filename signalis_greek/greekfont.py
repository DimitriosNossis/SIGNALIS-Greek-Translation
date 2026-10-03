"""Give Silver_JPC a Greek alphabet in the style and size of its own Latin letters.

Silver_JPC is the TextMeshPro fallback font that supplies Greek in SIGNALIS. Its stock Greek is
the JIS set: twice as wide as Latin, slanted, and missing tonos vowels and final sigma. Here every
Greek code point gets a new 5px-wide pixel glyph on Silver's Latin grid (cap height 9, x-height 6,
descender 3); letters identical to Latin capitals reuse the Latin glyph's atlas pixels.

  Silver_JPC      raster, 16pt, 1 atlas px = 1 font px
  Silver_JPC_SDF  SDF,    27pt (x1.6875), padding 5; generated from the same bitmaps
"""
import struct

import numpy as np
from scipy.ndimage import distance_transform_edt

from .tmpfont import find_glyphs

SDF_SCALE = 27 / 16
SDF_PAD = 5
CAP = 9  # cap height; grid row r is (CAP - r) px above the baseline, rows 9.. are descender

# Greek letter -> Latin glyph with the same shape (reused as-is)
SAME_AS_LATIN = {"Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K", "Μ": "M",
                 "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X", "ο": "o", "ν": "v"}

# New glyphs: (top grid row, rows). '#' = ink. Rows 0-8 cap zone, 3-8 x-height, 9-11 descender.
DRAWN = {
    "Γ": (0, "#####|#....|#....|#....|#....|#....|#....|#....|#...."),
    "Δ": (0, "..#..|..#..|.#.#.|.#.#.|.#.#.|#...#|#...#|#...#|#####"),
    "Θ": (0, ".###.|#...#|#...#|#...#|#####|#...#|#...#|#...#|.###."),
    "Λ": (0, "..#..|..#..|.#.#.|.#.#.|.#.#.|#...#|#...#|#...#|#...#"),
    "Ξ": (0, "#####|.....|.....|.....|.###.|.....|.....|.....|#####"),
    "Π": (0, "#####|#...#|#...#|#...#|#...#|#...#|#...#|#...#|#...#"),
    "Σ": (0, "#####|#....|.#...|..#..|...#.|..#..|.#...|#....|#####"),
    "Φ": (0, "..#..|..#..|.###.|#.#.#|#.#.#|#.#.#|.###.|..#..|..#.."),
    "Ψ": (0, "#.#.#|#.#.#|#.#.#|#.#.#|.###.|..#..|..#..|..#..|..#.."),
    "Ω": (0, ".###.|#...#|#...#|#...#|#...#|#...#|.#.#.|.#.#.|##.##"),
    "α": (3, ".##.#|#..#.|#..#.|#..#.|#..#.|.##.#"),
    "β": (0, ".##..|#..#.|#..#.|###..|#..#.|#...#|#...#|#...#|####.|#....|#...."),
    "γ": (3, "#...#|#...#|.#.#.|.#.#.|..#..|..#..|..#..|..#.."),
    "δ": (0, ".###.|#....|.#...|.##..|#..#.|#...#|#...#|#...#|.###."),
    "ε": (3, ".####|#....|###..|#....|#....|.####"),
    "ζ": (0, "####.|..#..|.#...|#....|#....|#....|#....|.###.|....#|..##."),
    "η": (3, "#.##.|##..#|#...#|#...#|#...#|#...#|....#|....#"),
    "θ": (0, ".##.|#..#|#..#|#..#|####|#..#|#..#|#..#|.##."),
    "ι": (3, ".#.|.#.|.#.|.#.|.#.|..#"),
    "κ": (3, "#..#.|#.#..|##...|#.#..|#..#.|#...#"),
    "λ": (0, "#....|.#...|.#...|..#..|..#..|.#.#.|.#.#.|#...#|#...#"),
    "μ": (3, "#...#|#...#|#...#|#...#|#..##|###.#|#....|#...."),
    "ξ": (0, "#####|.#...|#....|.###.|.#...|#....|#....|.###.|....#|..##."),
    "π": (3, "#####|.#.#.|.#.#.|.#.#.|.#.#.|.#..#"),
    "ρ": (3, ".###.|#...#|#...#|#...#|##..#|#.##.|#....|#...."),
    "σ": (3, ".####|#..#.|#...#|#...#|#...#|.###."),
    "ς": (3, "..###|.#...|#....|#....|.###.|....#|..##."),
    "τ": (3, "#####|..#..|..#..|..#..|..#..|...##"),
    "υ": (3, "#...#|#...#|#...#|#...#|#...#|.###."),
    "φ": (2, "..#..|.###.|#.#.#|#.#.#|#.#.#|#.#.#|.###.|..#..|..#.."),
    "χ": (3, "#...#|.#.#.|.#.#.|..#..|.#.#.|.#.#.|#...#"),
    "ψ": (2, "..#..|#.#.#|#.#.#|#.#.#|#.#.#|.###.|..#..|..#..|..#.."),
    "ω": (3, "#...#|#...#|#.#.#|#.#.#|#.#.#|.#.#."),
}

ACUTE = "...#.|..#.."        # Silver's á accent, sits on grid rows 0-1 above x-height letters
DIAERESIS = ".#.#.|.#.#."    # Silver's ä dots
DIA_ACUTE = "...#.|#.#.#"    # dialytika + tonos

LOWER_TONOS = {"ά": "α", "έ": "ε", "ή": "η", "ί": "ι", "ό": "ο", "ύ": "υ", "ώ": "ω"}
LOWER_DIA = {"ϊ": "ι", "ϋ": "υ"}
LOWER_DIA_TONOS = {"ΐ": "ι", "ΰ": "υ"}
UPPER_TONOS = {"Ά": "Α", "Έ": "Ε", "Ή": "Η", "Ί": "Ι", "Ό": "Ο", "Ύ": "Υ", "Ώ": "Ω"}
UPPER_DIA = {"Ϊ": "Ι", "Ϋ": "Υ"}


# The game upper-cases some UI text itself (IL2CPP char.ToUpper, table in global-metadata.dat):
# ά→Ά keeps the tonos and ς is left as ς, both wrong in Greek capitals. So the patcher rewrites
# Greek text to spare code points whose upper-case partners we are free to draw:
#   ς → ϲ (U+03F2, upper Ϲ U+03F9 drawn as Σ)
#   word-initial Ά..Ώ → Coptic ϣ..ϯ (upper Ϣ..Ϯ drawn as plain Α..Ω)
#   ΐ → ϙ (upper Ϙ drawn as Ϊ)
# and the real tonos capitals Ά..Ώ (only produced by upper-casing ά..ώ) are drawn without tonos.
RUNTIME_SUBST = {"ς": "ϲ", "ΐ": "ϙ",
                 "Ά": "ϣ", "Έ": "ϥ", "Ή": "ϧ", "Ί": "ϩ",
                 "Ό": "ϫ", "Ύ": "ϭ", "Ώ": "ϯ"}
UPPER_OF = {"ϲ": "Ϲ", "ϙ": "Ϙ",
            "ϣ": "Ϣ", "ϥ": "Ϥ", "ϧ": "Ϧ", "ϩ": "Ϩ",
            "ϫ": "Ϫ", "ϭ": "Ϭ", "ϯ": "Ϯ"}
PLAIN_CAPS = {"Ά": "Α", "Έ": "Ε", "Ή": "Η", "Ί": "Ι", "Ό": "Ο", "Ύ": "Υ", "Ώ": "Ω"}


def to_runtime(text):
    return "".join(RUNTIME_SUBST.get(c, c) for c in text)


def bits(s):
    return np.array([[255 if c == "#" else 0 for c in r] for r in s.split("|")], np.uint8)


class Font:
    """Legacy TMP_FontAsset raw bytes + its atlas (2D uint8 alpha, top row first)."""

    def __init__(self, raw, atlas):
        self.raw, self.atlas = raw, atlas
        self.count, self.list_off = find_glyphs(raw)
        self.glyphs = [list(struct.unpack_from("<i8f", raw, self.list_off + 4 + i * 36))
                       for i in range(self.count)]
        self.by_char = {g[0]: g for g in self.glyphs}
        self.claimed = []  # atlas rects written by us

    def crop(self, ch):
        _, x, y, w, h, *_ = self.by_char[ord(ch)]
        return self.atlas[int(y):int(np.ceil(y + h)), int(x):int(np.ceil(x + w))].copy()

    def place(self, bw, bh, pad):
        """Find a spot for a bw x bh glyph at least pad px from any other glyph; return its top-left."""
        occ = self.atlas >= 128
        for _, x, y, w, h, *_ in self.glyphs + self.claimed:
            if w > 0:
                occ[int(y):int(np.ceil(y + h)) + 1, int(x):int(np.ceil(x + w)) + 1] = True
        H, W = occ.shape
        need_h, need_w = bh + 2 * pad, bw + 2 * pad
        sat = np.pad(occ.astype(np.int32).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
        for y in range(0, H - need_h):
            row = sat[y + need_h, need_w:] - sat[y, need_w:] - sat[y + need_h, :-need_w] + sat[y, :-need_w]
            free = np.flatnonzero(row[:W - need_w] == 0)
            if free.size:
                return int(free[0]) + pad, y + pad
        raise RuntimeError("atlas full")

    def free_glyphs(self, codepoints, pad):
        """Erase glyphs' atlas pixels (keeping other glyphs' padding) and detach them."""
        H, W = self.atlas.shape
        doomed = [g for g in self.glyphs if g[0] in codepoints and g[3] > 0]
        keep = np.zeros((H, W), bool)
        for g in self.glyphs:
            if g[0] not in codepoints:
                _, x, y, w, h = g[:5]
                keep[max(0, int(y) - pad):int(np.ceil(y + h)) + pad + 1,
                     max(0, int(x) - pad):int(np.ceil(x + w)) + pad + 1] = True
        for g in doomed:
            _, x, y, w, h = g[:5]
            ys = slice(max(0, int(y) - pad), int(np.ceil(y + h)) + pad + 1)
            xs = slice(max(0, int(x) - pad), int(np.ceil(x + w)) + pad + 1)
            self.atlas[ys, xs] = np.where(keep[ys, xs], self.atlas[ys, xs], 0)
            g[1:5] = [0.0, 0.0, 0.0, 0.0]

    def set_glyph(self, ch, x, y, w, h, xoff, yoff, adv):
        g = [ord(ch), float(x), float(y), float(w), float(h), float(xoff), float(yoff), float(adv), 1.0]
        if ord(ch) in self.by_char:
            self.by_char[ord(ch)][:] = g
        else:
            self.glyphs.append(g)
            self.by_char[ord(ch)] = g

    def alias(self, ch, source):
        """Make ch render exactly like an existing glyph (same atlas pixels and metrics)."""
        self.set_glyph(ch, *self.by_char[ord(source)][1:8])

    def build(self):
        out = bytearray(self.raw[:self.list_off])
        out += struct.pack("<i", len(self.glyphs))
        for g in self.glyphs:
            out += struct.pack("<i8f", *g)
        out += self.raw[self.list_off + 4 + self.count * 36:]
        # FaceInfo (20 x 4 bytes) and the atlas PPtr (12 bytes) sit right before the glyph list;
        # characterCount is FaceInfo's 3rd field.
        count_off = self.list_off - 12 - 80 + 8
        assert struct.unpack_from("<i", self.raw, count_off)[0] == self.count
        struct.pack_into("<i", out, count_off, len(self.glyphs))
        return bytes(out)


def stack(mark, base, gap=1):
    """Put a mark centred above a bitmap."""
    mh, mw = mark.shape
    bh, bw = base.shape
    w = max(mw, bw)
    img = np.zeros((mh + gap + bh, w), np.uint8)
    bx, mx = (w - bw) // 2, (w - mw + 1) // 2
    img[mh + gap:, bx:bx + bw] = base
    img[:mh, mx:mx + mw] = np.maximum(img[:mh, mx:mx + mw], mark)
    return img, bx


def greek_bitmaps(raster):
    """Return {char: (bitmap, xoff, yoff, adv)} in raster pixel units, plus {char: latin} reuses."""
    out = {}
    for ch, (top, rows) in DRAWN.items():
        b = bits(rows)
        out[ch] = (b, 0, CAP - top, b.shape[1] + 1)

    def base(ch):
        if ch in out:
            return out[ch]
        g = raster.by_char[ord(SAME_AS_LATIN[ch])]
        return raster.crop(SAME_AS_LATIN[ch]), g[5], g[6], g[7]

    for table, mark in ((LOWER_TONOS, ACUTE), (LOWER_DIA, DIAERESIS), (LOWER_DIA_TONOS, DIA_ACUTE)):
        for ch, b in table.items():
            img, xoff, yoff, adv = base(b)
            m = bits(mark)
            if img.shape[1] < m.shape[1]:   # narrow ι: trim the mark to its ink
                cols = np.flatnonzero(m.any(0))
                m = m[:, cols.min():cols.max() + 1]
            new, shift = stack(m, img)
            out[ch] = (new, xoff - shift, yoff + (new.shape[0] - img.shape[0]), max(adv, new.shape[1] + 1))
    for ch, b in UPPER_TONOS.items():
        # capital tonos sits to the upper left of the letter
        img, xoff, yoff, adv = base(b)
        m = bits(".#|#.")
        new = np.zeros((img.shape[0], m.shape[1] + 1 + img.shape[1]), np.uint8)
        new[:, m.shape[1] + 1:] = img
        new[:m.shape[0], :m.shape[1]] = m
        out[ch] = (new, xoff, yoff, adv + m.shape[1] + 1)
    for ch, b in UPPER_DIA.items():
        img, xoff, yoff, adv = base(b)
        new, shift = stack(bits(".#.#."), img, gap=1)
        out[ch] = (new, xoff - shift, yoff + 2, max(adv, new.shape[1] + 1))
    return out


def sdf_from_bitmap(img, k=SDF_SCALE, pad=SDF_PAD, oversample=8, spread=6.0):
    """Render a 1-bit pixel bitmap as a TMP SDF tile (shape scaled by k, padded by pad)."""
    bh, bw = img.shape
    w, h = bw * k, bh * k
    tw, th = int(np.ceil(w)) + 2 * pad, int(np.ceil(h)) + 2 * pad
    S = oversample
    ys, xs = np.mgrid[0:th * S, 0:tw * S]
    fx = ((xs + 0.5) / S - pad) / k
    fy = ((ys + 0.5) / S - pad) / k
    hi = np.zeros((th * S, tw * S), bool)
    inside = (fx >= 0) & (fy >= 0) & (fx < bw) & (fy < bh)
    hi[inside] = img[fy[inside].astype(int), fx[inside].astype(int)] > 127
    d = (distance_transform_edt(hi) - distance_transform_edt(~hi)) / S
    d = d.reshape(th, S, tw, S).mean(axis=(1, 3))
    return (np.clip(0.5 + d / (2 * spread), 0, 1) * 255).round().astype(np.uint8), w, h


def calibrate_spread(raster, sdf, ch="a"):
    """Pick the SDF spread that best reproduces an existing glyph."""
    g = sdf.by_char[ord(ch)]
    x, y = int(g[1]), int(g[2])
    ref = sdf.atlas[y - SDF_PAD:y - SDF_PAD + 40, x - SDF_PAD:x - SDF_PAD + 40].astype(float)
    best = None
    for spread in np.arange(2.0, 10.01, 0.5):
        tile, _, _ = sdf_from_bitmap(raster.crop(ch), spread=spread)
        r = ref[:tile.shape[0], :tile.shape[1]]
        err = np.abs(r - tile[:r.shape[0], :r.shape[1]]).mean()
        if best is None or err < best[0]:
            best = (err, spread)
    return best[1], best[0]


def add_greek(raster, sdf):
    """Install the Greek alphabet in both fonts. Returns the list of characters set."""
    spread, _ = calibrate_spread(raster, sdf)
    old_greek = set(range(0x370, 0x400))
    raster.free_glyphs(old_greek, pad=1)
    sdf.free_glyphs(old_greek, pad=SDF_PAD)
    for ch, latin in SAME_AS_LATIN.items():
        for f in (raster, sdf):
            g = f.by_char[ord(latin)]
            f.set_glyph(ch, *g[1:8])
    bitmaps = greek_bitmaps(raster)
    for ch, (img, xoff, yoff, adv) in bitmaps.items():
        h, w = img.shape
        x, y = raster.place(w, h, pad=3)
        raster.atlas[y:y + h, x:x + w] = img
        raster.claimed.append([0, x, y, w, h])
        raster.set_glyph(ch, x, y, w, h, xoff, yoff, adv)

        tile, sw, sh = sdf_from_bitmap(img, spread=spread)
        th, tw = tile.shape
        x, y = sdf.place(tw - 2 * SDF_PAD, th - 2 * SDF_PAD, pad=SDF_PAD + 1)
        region = sdf.atlas[y - SDF_PAD:y - SDF_PAD + th, x - SDF_PAD:x - SDF_PAD + tw]
        region[:] = np.maximum(region, tile)
        sdf.claimed.append([0, x, y, sw, sh])
        sdf.set_glyph(ch, x, y, sw, sh, xoff * SDF_SCALE, yoff * SDF_SCALE, adv * SDF_SCALE)
    for f in (raster, sdf):
        # spare code points: lower = the accented form, upper = what Greek capitals need
        for real, spare in RUNTIME_SUBST.items():
            f.alias(spare, real)
        for spare, upper in UPPER_OF.items():
            real = next(r for r, s in RUNTIME_SUBST.items() if s == spare)
            f.alias(upper, {"ς": "Σ", "ΐ": "Ϊ"}.get(real) or PLAIN_CAPS[real])
        # real tonos capitals only appear after the game upper-cases ά..ώ: no tonos in capitals
        for accented, plain in PLAIN_CAPS.items():
            f.alias(accented, plain)
    return list(SAME_AS_LATIN) + list(bitmaps) + list(RUNTIME_SUBST.values()) + list(UPPER_OF.values())


# SignalisFive: 5px all-caps pixel font (lowercase letters are drawn as capitals too).
FIVE_SAME = {"Α": "A", "Β": "B", "Γ": "Г", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
             "Μ": "M", "Ν": "N", "Ο": "O", "Π": "П", "Ρ": "P", "Τ": "T", "Υ": "Y", "Φ": "Ф", "Χ": "X"}
FIVE_DRAWN = {
    "Δ": "..#..|.#.#.|.#.#.|#...#|#####",
    "Θ": ".###.|#...#|#####|#...#|.###.",
    "Λ": "..#..|.#.#.|.#.#.|#...#|#...#",
    "Ξ": "#####|.....|.###.|.....|#####",
    "Σ": "#####|.#...|..#..|.#...|#####",
    "Ψ": "#.#.#|#.#.#|#####|..#..|..#..",
    "Ω": "#####|#...#|#...#|.#.#.|##.##",
}


def greek_capital(ch):
    """The plain capital a Greek (or spare) code point should look like in an all-caps font."""
    import unicodedata
    for real, spare in RUNTIME_SUBST.items():
        if ch in (spare, UPPER_OF[spare]):
            ch = real
    if ch in "ςσ":
        return "Σ"
    base = unicodedata.normalize("NFD", ch)[0]
    return base.upper()


def add_greek_caps_five(font):
    """Give SignalisFive every Greek code point we use, all rendered as 5px capitals."""
    ref = font.by_char[ord("A")]
    for ch, rows in FIVE_DRAWN.items():
        img = bits(rows)
        h, w = img.shape
        x, y = font.place(w, h, pad=2)
        font.atlas[y:y + h, x:x + w] = img
        font.claimed.append([0, x, y, w, h])
        font.set_glyph(ch, x, y, w, h, 0, ref[6], ref[7])
    for ch, src in FIVE_SAME.items():
        font.alias(ch, src)
    codepoints = (list(range(0x386, 0x390)) + list(range(0x390, 0x3AA)) + list(range(0x3AA, 0x3D0))
                  + [ord(c) for c in list(RUNTIME_SUBST.values()) + list(UPPER_OF.values())])
    added = 0
    for cp in codepoints:
        ch = chr(cp)
        try:
            cap = greek_capital(ch)
        except IndexError:
            continue
        if ord(cap) in font.by_char and cp not in font.by_char:
            font.alias(ch, cap)
            added += 1
    return added


# ---------------------------------------------------------------- door / ladder prompt sprites
# Door_interactions texture: English labels are 16x64 strips, text rotated (reads bottom to top),
# 5px SignalisFive letters, black on a coloured box with a 1px black border.
DOOR_STRIPS = {  # sprite index: (x, top row, Greek label)
    12: (96, 0, "ΒΛΑΒΗ"),        # NO ENTRY  (broken door, 故障)
    13: (112, 0, "ΚΛΕΙΔΙ"),      # NEED KEY
    14: (128, 0, "ΑΝΕΒΑ"),       # CLIMB UP
    17: (144, 0, "ΚΑΤΕΒΑ"),      # CLIMB DOWN
    18: (160, 0, "ΠΑΝΩ"),        # GO UP
    19: (176, 0, "ΚΑΤΩ"),        # GO DOWN
    24: (160, 64, "ΚΛΕΙΣΤΟ"),    # LOCKED
    23: (176, 64, "ΠΗΔΑ ΚΑΤΩ"),  # DROP DOWN
}


def label_bitmaps(five, text):
    """Glyph bitmaps (5 rows high) for text in the patched SignalisFive font; space = 5px gap."""
    out = []
    for ch in text:
        if ch == " ":
            out.append(np.zeros((5, 5), np.uint8))
        else:
            out.append(five.crop(ch))
    return out


def draw_door_labels(img, five):
    """img: RGBA array of Door_interactions (top row first). Redraws the English strips in Greek."""
    for idx, (x, top, text) in DOOR_STRIPS.items():
        strip = img[top:top + 64, x:x + 16]
        alpha = strip[..., 3] > 0
        rows = np.where(alpha.any(1))[0]
        r0, c0 = rows.min(), np.where(alpha.any(0))[0].min()
        fill = strip[r0 + 1, c0 + 1].copy()
        border = strip[r0, c0].copy()
        glyphs = label_bitmaps(five, text)
        text_len = sum(g.shape[1] for g in glyphs) + len(glyphs) - 1
        box_len = text_len + 6                      # border + 2px margin on each side
        assert box_len <= 62, f"label too long: {text}"
        b0 = 31 - box_len // 2
        b1 = b0 + box_len - 1
        strip[:] = 0
        strip[b0:b1 + 1, 2:14] = border
        strip[b0 + 1:b1, 3:13] = fill
        cursor = b1 - 3                             # text starts at the bottom, reads upwards
        for g in glyphs:
            gh, gw = g.shape
            for gy in range(gh):
                for gx in range(gw):
                    if g[gy, gx] > 127:
                        strip[cursor - gx, 6 + gy] = border
            cursor -= gw + 1
    return img


INSPECT_LABEL = "ΕΛΕΓΞΕ"


def draw_inspect_label(img, five, text=INSPECT_LABEL):
    """Interaction_inspect texture (48x16): horizontal 'INSPECT' box redrawn with Greek text."""
    alpha = img[..., 3] > 0
    rows = np.where(alpha.any(1))[0]
    cols = np.where(alpha.any(0))[0]
    r0, r1, c0 = rows.min(), rows.max(), cols.min()
    fill, border = img[r0 + 1, c0 + 1].copy(), img[r0, c0].copy()
    glyphs = label_bitmaps(five, text)
    text_w = sum(g.shape[1] for g in glyphs) + len(glyphs) - 1
    box_w = text_w + 6
    H, W = img.shape[:2]
    assert box_w <= W, f"label too long: {text}"
    b0 = (W - box_w) // 2
    img[:] = 0
    img[r0:r1 + 1, b0:b0 + box_w] = border
    img[r0 + 1:r1, b0 + 1:b0 + box_w - 1] = fill
    x, y = b0 + 3, r0 + 3                     # 2px margin inside the border, like the original
    for g in glyphs:
        gh, gw = g.shape
        mask = g > 127
        img[y:y + gh, x:x + gw][mask] = border
        x += gw + 1
    return img
