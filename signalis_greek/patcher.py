"""SIGNALIS Greek translation patcher.

Replaces the Russian ("ru") language slot of SIGNALIS with Greek and adds the Greek letters the
game's fonts are missing. Works on the player's own copy of the game: nothing from the game is
shipped with this tool.

The original data.unity3d is kept next to it as data.unity3d.original, and every run patches from
that backup, so the patcher can be run again safely (e.g. after editing the translation).
"""
import argparse
import csv
import hashlib
import os
import shutil
import sys

import numpy as np
import UnityPy
from PIL import Image

from .greekfont import Font, add_greek, add_greek_caps_five, to_runtime
from .locdata import build, parse, tables

VERSION = "0.9.1"
SLOT = "ru"
CONTAINER = "LocalizerDataContainer"
FONTS = ("Silver_JPC", "Silver_JPC_SDF", "SignalisFive_rasterHinted16")
TECHNICAL_KEYS = {"LanguageCode", "LanguageIdentifier"}  # keep the slot's own values
BACKUP_SUFFIX = ".original"
MARKER_SUFFIX = ".greek"  # holds the SHA-256 of the file we wrote


def resource(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, *parts)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- finding the game

def steam_libraries():
    roots = []
    try:
        import winreg
        for hive, key in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                          (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
            try:
                with winreg.OpenKey(hive, key) as k:
                    for value in ("SteamPath", "InstallPath"):
                        try:
                            roots.append(winreg.QueryValueEx(k, value)[0])
                        except OSError:
                            pass
            except OSError:
                pass
    except ImportError:
        pass
    roots += [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"]
    libs = []
    for root in roots:
        root = os.path.normpath(root)
        libs.append(root)
        vdf = os.path.join(root, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            for line in open(vdf, encoding="utf-8", errors="ignore"):
                parts = line.strip().split('"')
                if len(parts) >= 4 and parts[1] == "path":
                    libs.append(os.path.normpath(parts[3].replace("\\\\", "\\")))
    return list(dict.fromkeys(libs))


def data_file(game_dir):
    return os.path.join(game_dir, "SIGNALIS_Data", "data.unity3d")


def find_game(given=None):
    if given:
        return given if os.path.exists(data_file(given)) else None
    for lib in steam_libraries():
        candidate = os.path.join(lib, "steamapps", "common", "SIGNALIS")
        if os.path.exists(data_file(candidate)):
            return candidate
    return None


# ---------------------------------------------------------------- patching

def load_translation():
    with open(resource("translation", "el.csv"), encoding="utf-8-sig", newline="") as f:
        return {r["key"]: r["el"] for r in csv.DictReader(f) if r["el"]}


def patch_fonts(behaviours, textures):
    fonts = {}
    for name in FONTS:
        tex = textures[name + " Atlas"].read()
        atlas = np.array(tex.image.convert("RGBA"))[..., 3].copy()
        fonts[name] = (Font(behaviours[name].get_raw_data(), atlas), tex)
    add_greek(fonts["Silver_JPC"][0], fonts["Silver_JPC_SDF"][0])
    add_greek_caps_five(fonts["SignalisFive_rasterHinted16"][0])
    for name, (font, tex) in fonts.items():
        behaviours[name].set_raw_data(font.build())
        img = np.zeros(font.atlas.shape + (4,), np.uint8)
        img[..., 3] = font.atlas
        tex.image = Image.fromarray(img, "RGBA")
        tex.save()


def patch_bundle(source, target):
    print("  Loading game data...")
    env = UnityPy.load(source)
    behaviours, textures = {}, {}
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            name = o.peek_name()
            if name in {CONTAINER, *FONTS}:
                if name in behaviours:
                    raise RuntimeError(f"unexpected game data (duplicate {name})")
                behaviours[name] = o
        elif o.type.name == "Texture2D":
            name = o.peek_name()
            if name in {f + " Atlas" for f in FONTS}:
                textures[name] = o
    missing = ({CONTAINER, *FONTS} - set(behaviours)) | ({f + " Atlas" for f in FONTS} - set(textures))
    if missing:
        raise RuntimeError(f"this version of SIGNALIS is not supported (missing {sorted(missing)})")

    raw = behaviours[CONTAINER].get_raw_data()
    d = parse(raw)
    if build(d) != raw:
        raise RuntimeError("this version of SIGNALIS is not supported (text format changed)")
    all_tables = tables(d)
    en, slot = all_tables["en"], all_tables[SLOT]

    greek = load_translation()
    unknown = [k for k in greek if k not in en]
    if unknown:
        print(f"  Note: {len(unknown)} translated strings are not in this game version (ignored).")

    print("  Adding Greek letters to the fonts...")
    patch_fonts(behaviours, textures)

    print("  Writing the Greek text...")
    pairs, done = [], 0
    for k, v in en.items():
        if k in TECHNICAL_KEYS:
            text = slot[k]
        elif greek.get(k):
            text = to_runtime(greek[k])
            done += 1
        else:
            text = v
        pairs.append((k, text))
    for lang in d["langs"]:
        if lang[0] == SLOT:
            lang[1] = pairs
    behaviours[CONTAINER].set_raw_data(build(d))

    print("  Saving (this takes 1-2 minutes)...")
    data = env.file.save(packer="lz4")
    tmp = target + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, target)
    return done, len(en)


def run(args):
    print(f"SIGNALIS - Ελληνική μετάφραση / Greek translation  v{VERSION}\n")
    game = find_game(args.game)
    while not game:
        if args.game:
            print(f"SIGNALIS not found in: {args.game}")
        path = input("SIGNALIS folder (e.g. C:\\...\\steamapps\\common\\SIGNALIS): ").strip().strip('"')
        game = find_game(path)
    data = data_file(game)
    backup, marker = data + BACKUP_SUFFIX, data + MARKER_SUFFIX
    print(f"Game: {game}")

    if args.restore:
        if not os.path.exists(backup):
            print("No backup found: the game is not patched (or the backup was deleted).")
            return 1
        if not (os.path.exists(marker) and open(marker).read().strip() == sha256(data)):
            # Steam replaced the file since we patched it: it is already original (and newer)
            for p in (backup, marker):
                if os.path.exists(p):
                    os.remove(p)
            print("The game files are already original (updated by Steam). Removed the old backup.")
            return 0
        shutil.copyfile(backup, data)
        for p in (backup, marker):
            os.remove(p)
        print("Original game files restored. / Επαναφέρθηκαν τα αρχικά αρχεία.")
        return 0

    ours = os.path.exists(marker) and open(marker).read().strip() == sha256(data)
    if not ours:
        # the game file is original (first run, or Steam updated/verified it): back it up
        print("Backing up the original game file...")
        shutil.copyfile(data, backup)
    elif not os.path.exists(backup):
        print("The game is patched but the backup is missing. Use Steam > Verify integrity of game files,")
        print("then run this patcher again.")
        return 1

    print("Patching...")
    done, total = patch_bundle(backup, data)
    with open(marker, "w") as f:
        f.write(sha256(data))
    print(f"\nDone! {done}/{total} strings in Greek.")
    print("In the game: Settings > Language > Ελληνικά")
    print("Στο παιχνίδι: Ρυθμίσεις > Γλώσσα > Ελληνικά")
    return 0


def utf8_console():
    """Greek text must not crash on Windows consoles that default to a legacy code page."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main():
    utf8_console()
    ap = argparse.ArgumentParser(description="SIGNALIS Greek translation patcher")
    ap.add_argument("--restore", action="store_true", help="put the original game files back")
    ap.add_argument("--game", help="SIGNALIS install folder (found automatically if omitted)")
    args = ap.parse_args()
    frozen = getattr(sys, "frozen", False)
    if frozen and not args.restore and len(sys.argv) == 1:
        choice = input("1 = Install Greek / Εγκατάσταση\n2 = Restore original / Επαναφορά\n> ").strip()
        args.restore = choice == "2"
        print()
    try:
        code = run(args)
    except Exception as e:  # show a readable message instead of a traceback window closing
        print(f"\nError: {e}")
        code = 1
    if frozen:
        input("\nPress Enter to exit / Πατήστε Enter για έξοδο")
    return code
