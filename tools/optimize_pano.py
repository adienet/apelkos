#!/usr/bin/env python3
"""
Perkecil foto panorama 360 (equirectangular) supaya cepat dimuat di web.

Pakai:
  python3 tools/optimize_pano.py images/360/1.jpg
  python3 tools/optimize_pano.py images/360/1.jpg -o images/360/1-web.jpg

Metadata penting TIDAK dibuang:
  - XMP GPano (ProjectionType=equirectangular) supaya file tetap
    dikenali sebagai photo sphere / panorama 360
  - EXIF (kamera, tanggal, GPS)

Kenapa perlu diperkecil:
  Foto 7680 x 3840 dari kamera Insta360 bisa 12-16 MB. Di koneksi
  seluler itu berat dan banyak pengunjung akan menunggu lama atau
  belum sempat dibuka. Versi 5120-7680 px dengan progressive JPEG
  cukup 2-3 MB dengan kualitas visual hampir identik.
"""
import os
import sys
from PIL import Image

QUALITY = 82          # 78-85 sweet spot panorama, FILE smaller bigger
MAX_WIDTH = 7680      # jangan di atas ini, 8K sudah lebih dari cukup


def optimize(src, dst=None, quality=QUALITY, max_width=MAX_WIDTH):
    dst = dst or (os.path.splitext(src)[0] + "-web.jpg")
    im = Image.open(src)

    w, h = im.size
    ratio = w / h
    if abs(ratio - 2.0) > 0.03:
        raise SystemExit(
            f"PERINGATAN: rasio {w}x{h} = {ratio:.3f}:1, bukan 2:1.\n"
            "Foto panorama 360 HARUS lebar 2x tinggi. Kalau ini bukan 2:1,\n"
            "kemungkinan besar mode dual-fisheye -> export ulang dari\n"
            "Insta360 Studio ke JPG equirectangular."
        )

    if w > max_width:
        nw = max_width
        im = im.resize((nw, nw // 2), Image.LANCZOS)

    kw = dict(quality=quality, optimize=True, progressive=True)
    if im.info.get("xmp"):
        kw["xmp"] = im.info["xmp"]
    if im.info.get("exif"):
        kw["exif"] = im.info["exif"]
    im.save(dst, "JPEG", **kw)

    before = os.path.getsize(src) / 1048576
    after = os.path.getsize(dst) / 1048576
    saved = 100 * (1 - after / before) if before else 0
    print(f"  {os.path.basename(src)}  {w}x{h}  {before:.2f} MB")
    print(f"  {os.path.basename(dst)}  {im.size[0]}x{im.size[1]}  "
          f"{after:.2f} MB   hemat {saved:.0f}%")
    if im.size[0] == w:
        print("  (resolusi dipertahankan, hanya re-kompres)")
    else:
        print(f"  (diperkecil ke lebar {im.size[0]} px)")
    return dst


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    src = args[0]
    dst = None
    if len(args) > 1:
        dst = args[1]
    print("Memproses panorama 360...")
    optimize(src, dst)
