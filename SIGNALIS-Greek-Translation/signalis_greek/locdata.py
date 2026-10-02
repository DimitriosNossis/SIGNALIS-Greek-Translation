"""Read/write the SIGNALIS LocalizerDataContainer MonoBehaviour (raw serialized bytes).

Layout (Unity serialization, little-endian, strings = int32 length + UTF-8 + pad to 4):
  header ............ bytes up to the key list (MonoBehaviour base fields + m_Name)
  keys .............. string[]                    (1919 keys)
  languages ......... int32 count (9), then "Comment", "" (an empty first entry),
                      then 8 x { string code; int32 n; n x { string key; string value } }
  tail .............. remaining bytes, copied verbatim
"""
import struct

KEYS_OFFSET = 56


def _ri(b, o):
    return struct.unpack_from("<i", b, o)[0], o + 4


def _rs(b, o):
    n, o = _ri(b, o)
    return b[o:o + n].decode("utf-8"), (o + n + 3) & ~3


def _ws(s):
    e = s.encode("utf-8")
    return struct.pack("<i", len(e)) + e + b"\0" * ((-len(e)) % 4)


def parse(b):
    o = KEYS_OFFSET
    nkeys, o = _ri(b, o)
    for _ in range(nkeys):
        _, o = _rs(b, o)
    langs_offset = o
    nl, o = _ri(b, o)
    comment, o = _rs(b, o)
    empty, o = _rs(b, o)
    langs = []
    for _ in range(nl - 1):
        code, o = _rs(b, o)
        n, o = _ri(b, o)
        pairs = []
        for _ in range(n):
            k, o = _rs(b, o)
            v, o = _rs(b, o)
            pairs.append((k, v))
        langs.append([code, pairs])
    return {"head": b[:langs_offset], "nl": nl, "comment": comment, "empty": empty,
            "langs": langs, "tail": b[o:]}


def build(d):
    out = bytearray(d["head"])
    out += struct.pack("<i", d["nl"]) + _ws(d["comment"]) + _ws(d["empty"])
    for code, pairs in d["langs"]:
        out += _ws(code) + struct.pack("<i", len(pairs))
        for k, v in pairs:
            out += _ws(k) + _ws(v)
    out += d["tail"]
    return bytes(out)


def tables(d):
    return {code: dict(pairs) for code, pairs in d["langs"]}
