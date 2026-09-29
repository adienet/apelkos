#!/usr/bin/env python3
"""
Siapkan foto untuk website Apel Kos.

Membuat 3 versi dari setiap foto:
  <nama>-web.jpg   dipakai viewer 360 / lightbox
  thumbs/<nama>.jpg dipakai kartu pilihan 360 & grid galeri
  (file master aslinya TIDAK diubah, jangan dihapus dari komputer)

Pakai:
  # semua foto
  python3 tools/optimize_images.py

  # hanya satu foto
  python3 tools/optimize_images.py images/360/kontrakankamar1.jpg --long 200 --lat -5

  # hanya galeri (foto biasa)
  python3 tools/optimize_images.py images/galeri/dapur.jpg

 Kenapa perlu diperkecil:
  Foto panorama 7680x3840 dari kamera Insta360 beratnya 9-12 MB satu file.
  Enam panorama sekaligus = 60 MB. Di HP itu halaman galeri bisa sangat
  berat dan banyak pengunjung menutup tab sebelum selesai memuat.

 Metadata panorama (XMP GPano) TIDAK dibuang supaya file tetap
 dikenali sebagai photo sphere.
"""
import os
import sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- panorama 360 (equirectangular) ---
PANO_WEB_WIDTH = 5120   # 7680 -> 5120, hampir tidak kelihatan bedanya
PANO_WEB_QUALITY = 78

# --- foto biasa ---
FLAT_WEB_WIDTH = 1600
FLAT_WEB_QUALITY = 80

# --- thumbnail kartu ---
THUMB_W = 480
THUMB_H = 270          # 16:9
THUMB_QUALITY = 74
THUMB_VIEW_DEG = 96    # lebar sudut pandang thumbnail (derajat)


def human(size):
    return "%.2f MB" % (size / 1048576)


def fit_width(im, width):
    if im.width <= width:
        return im
    return im.resize((width, max(1, round(width * im.height / im.width))),
                     Image.LANCZOS)


def save_jpg(im, path, quality, keep_meta=False):
    kw = dict(quality=quality, optimize=True, progressive=True)
    if keep_meta:
        if im.info.get("xmp"):
            kw["xmp"] = im.info["xmp"]
        if im.info.get("exif"):
            kw["exif"] = im.info["exif"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.convert("RGB").save(path, "JPEG", **kw)
    return path


def pano_thumb(im, long_deg, lat_deg):
    """
    Potret sebagian bola 360 mengikuti arah pandang (long/lat),
    sama dengan setting awal viewer, supaya kartu choisirnya
   商人 resemble foto yang muncul saat dibuka.

    long 0   = tengah foto, 90 = ke kanan, 180 = belakang, 270/-90 = ke kiri
    lat  0   = horizon, negatif = sedikit menunduk
    """
    w, h = im.size
    view_w = THUMB_VIEW_DEG / 360.0
    # foto equirectangular selalu 2:1, jadi tinggi sudut = lebar sudut / 2
    view_h = view_w * 0.5

    x = (0.5 + (long_deg % 360) / 360.0) * w - view_w * w / 2
    y = (0.5 - lat_deg / 180.0) * h - view_h * h / 2

    left = int(round(min(max(x, 0), w - view_w * w)))
    top = int(round(min(max(y, 0), h - view_h * h)))
    right = int(round(min(left + view_w * w, w)))
    bottom = int(round(min(top + view_h * h, h)))

    crop = im.crop((left, top, right, bottom))
    return crop.resize((THUMB_W, THUMB_H), Image.LANCZOS)


def flat_thumb(im):
    """Potong tengah rasio 16:9 lalu perkecil."""
    w, h = im.size
    target = THUMB_W / THUMB_H
    if w / h > target:
        nw = int(round(h * target))
        left = (w - nw) // 2
        crop = im.crop((left, 0, left + nw, h))
    else:
        nh = int(round(w / target))
        top = int((h - nh) * 0.35)          # ambil sedikit ke atas (subjek)
        crop = im.crop((0, top, w, min(h, top + nh)))
    return crop.resize((THUMB_W, THUMB_H), Image.LANCZOS)


def process(src, long_deg=0, lat_deg=0):
    name = os.path.splitext(os.path.basename(src))[0]
    is_pano = os.sep + "360" + os.sep in src + os.sep
    rel = os.path.relpath(src, ROOT)
    if not os.path.exists(src):
        print("  Lewati (tidak ada):", rel)
        return

    im = Image.open(src)
    w, h = im.size
    before = os.path.getsize(src)

    if is_pano:
        ratio = w / h
        if abs(ratio - 2.0) > 0.03:
            print("  PERINGATAN %s rasio %dx%d = %.3f:1, bukan 2:1" % (name, w, h, ratio))
        web = save_jpg(fit_width(im, PANO_WEB_WIDTH),
                       os.path.join(ROOT, "images/360", name + "-web.jpg"),
                       PANO_WEB_QUALITY, keep_meta=True)
        save_jpg(pano_thumb(im, long_deg, lat_deg),
                 os.path.join(ROOT, "images/360/thumbs", name + ".jpg"),
                 THUMB_QUALITY)
    else:
        web = save_jpg(fit_width(im, FLAT_WEB_WIDTH),
                       os.path.join(ROOT, "images/galeri", name + "-web.jpg"),
                       FLAT_WEB_QUALITY)
        save_jpg(flat_thumb(im),
                 os.path.join(ROOT, "images/galeri/thumbs", name + ".jpg"),
                 THUMB_QUALITY)

    after = os.path.getsize(web)
    print("  %-24s %dx%d %8s  ->  %-30s %8s  (hemat %d%%)"
          % (name, w, h, human(before),
             os.path.relpath(web, ROOT), human(after),
             round(100 * (1 - after / before)) if before else 0))


def collect(args):
    if args:
        return [os.path.abspath(a) for a in args]
    found = []
    for folder in ("images/360", "images/galeri"):
        d = os.path.join(ROOT, folder)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.lower().endswith((".jpg", ".jpeg", ".png")) and "-web" not in f:
                found.append(os.path.join(d, f))
    return found


if __name__ == "__main__":
    argv = sys.argv[1:]
    long_deg, lat_deg = 0, 0
    if "--long" in argv:
        long_deg = float(argv[argv.index("--long") + 1])
    if "--lat" in argv:
        lat_deg = float(argv[argv.index("--lat") + 1])
    files = [a for a in argv if not a.startswith("-")]
    if "--long" in argv:
        files = [a for a in files if a not in (str(long_deg),)]
    if "--lat" in argv:
        files = [a for a in files if a not in (str(lat_deg),)]

    files = collect(files)
    if not files:
        raise SystemExit(__doc__)

    print("Memproses %d foto...\n" % len(files))
    for f in files:
        process(f, long_deg, lat_deg)
    print("\nSelesai. File master tidak diubah.")
