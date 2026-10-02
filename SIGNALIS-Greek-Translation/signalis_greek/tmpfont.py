"""Parse legacy TextMeshPro TMP_FontAsset glyph lists (TMP_Glyph = int id + 8 floats, 36 bytes)."""
import struct, os
def find_glyphs(b):
    best=None
    for o in range(0,len(b)-40,4):
        n=struct.unpack_from("<i",b,o)[0]
        if 1<=n<=40000 and o+4+n*36<=len(b):
            if all(struct.unpack_from("<f",b,o+4+i*36+32)[0]==1.0 for i in range(0,n,max(1,n//25))):
                if best is None or n>best[0]: best=(n,o)
    return best
def glyphs(b):
    r=find_glyphs(b)
    if not r: return None,[]
    n,o=r
    return o,[struct.unpack_from("<i8f",b,o+4+i*36) for i in range(n)]
