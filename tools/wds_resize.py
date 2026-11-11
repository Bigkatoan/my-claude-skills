#!/usr/bin/env python3
"""wds_resize - tải WebDataset (HF) từng shard bằng aria2c, resize ảnh rồi xoá shard gốc.

Không bao giờ giữ cả bộ gốc trên ổ: chỉ prefetch vài shard. Chạy lại = tiếp tục (bỏ qua shard đã xong).

  wds_resize.py hf:pixparse/cc3m-wds -o ~/datasets/vision/cc3m_224 --size 224 --mode stretch

mode:  stretch = resize thẳng về size x size, giữ toàn bộ nội dung (mặc định; kích thước gốc lưu trong json)
       crop    = resize cạnh ngắn -> size, center-crop (mất mép ảnh)
       pad     = giữ tỉ lệ, đệm đen thành size x size
Mỗi mẫu giữ nguyên .txt (caption) và .json (metadata gốc) + thêm trường resize vào json.
Cuối cùng ghi metadata.parquet (key, split, shard, caption, url, kích thước gốc, ...).
"""
import argparse, io, json, os, sys, tarfile, threading, queue, time, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adl import hf_files, download, human  # noqa: E402

IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")


def resize(data, size, mode, q):
    from PIL import Image, ImageOps
    im = Image.open(io.BytesIO(data))
    ow, oh = im.size
    if im.format == "JPEG":
        im.draft("RGB", (size * 2, size * 2))  # decode nhanh ở độ phân giải thấp hơn, vẫn >= 2x đích
    im = ImageOps.exif_transpose(im).convert("RGB")
    if mode == "crop":
        im = ImageOps.fit(im, (size, size), Image.BICUBIC, centering=(0.5, 0.5))
    elif mode == "stretch":
        im = im.resize((size, size), Image.BICUBIC)
    else:
        im = ImageOps.pad(im, (size, size), Image.BICUBIC, color=(0, 0, 0))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=q, subsampling=0)
    return buf.getvalue(), ow, oh


def add(tf, name, data):
    ti = tarfile.TarInfo(name); ti.size = len(data); ti.mtime = 0; ti.mode = 0o644
    tf.addfile(ti, io.BytesIO(data))


def process_shard(src, dst, size, mode, q):
    """src tar -> dst tar. Trả về (n_ok, n_fail, rows)."""
    groups, order = {}, []
    with tarfile.open(src) as tf:
        for m in tf:
            if not m.isfile():
                continue
            key, _, ext = m.name.rpartition(".")
            if key not in groups:
                groups[key] = {}; order.append(key)
            groups[key]["." + ext] = tf.extractfile(m).read()
    tmp = Path(str(dst) + ".tmp")
    ok = fail = 0; rows = []
    with tarfile.open(tmp, "w") as out:
        for key in order:
            g = groups.pop(key)
            img_ext = next((e for e in g if e in IMG_EXT), None)
            if not img_ext:
                fail += 1; continue
            try:
                jpg, ow, oh = resize(g[img_ext], size, mode, q)
            except Exception:
                fail += 1; continue
            meta = json.loads(g[".json"]) if ".json" in g else {}
            meta.update(resized_to=[size, size], resize_mode=mode, decoded_width=ow, decoded_height=oh)
            cap = g[".txt"].decode("utf-8", "replace") if ".txt" in g else meta.get("caption", "")
            add(out, f"{key}.jpg", jpg)
            add(out, f"{key}.txt", cap.encode())
            add(out, f"{key}.json", json.dumps(meta, ensure_ascii=False).encode())
            for e, d in g.items():  # giữ các trường khác nếu có (vd .cls)
                if e not in IMG_EXT and e not in (".txt", ".json"):
                    add(out, f"{key}{e}", d)
            ok += 1
            rows.append({"key": key, "caption": cap, "url": meta.get("url"),
                         "width": meta.get("original_width", meta.get("width", ow)),
                         "height": meta.get("original_height", meta.get("height", oh))})
    os.replace(tmp, dst)
    return ok, fail, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="hf:org/repo (WebDataset .tar)")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--size", type=int, default=224)
    ap.add_argument("--mode", choices=["stretch", "crop", "pad"], default="stretch")
    ap.add_argument("--quality", type=int, default=95)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--prefetch", type=int, default=12, help="số shard gốc tối đa nằm trên ổ cùng lúc")
    ap.add_argument("--include", action="append")
    a = ap.parse_args()

    out = Path(a.out).expanduser(); raw = out / "_raw"; (out / "_state").mkdir(parents=True, exist_ok=True)
    files, auth = hf_files(a.source[3:], "dataset", None, a.include, None)
    hdr = []
    if auth:
        from adl import hf_token
        hdr = [f"Authorization: Bearer {hf_token()}"]
    # file phụ (README, _info.json) tải thẳng vào out
    extras = [f for f in files if not f[1].endswith(".tar")]
    download(extras, out, hdr, quiet=True)
    shards = [f for f in files if f[1].endswith(".tar")]
    done = lambda rel: (out / "_state" / (rel.replace("/", "__") + ".json")).exists()
    todo = [s for s in shards if not done(s[1])]
    print(f"{len(shards)} shard ({human(sum(s[2] for s in shards))} gốc), còn {len(todo)}. "
          f"size={a.size} mode={a.mode} workers={a.workers}", flush=True)

    slots = threading.Semaphore(a.prefetch)
    ready = queue.Queue()

    def fetcher():
        for i in range(0, len(todo), 4):
            batch = todo[i:i + 4]
            for _ in batch:
                slots.acquire()
            for attempt in range(5):
                bad = download(batch, raw, hdr, jobs=4, quiet=True)
                if not bad:
                    break
                print(f"retry {attempt+1}: {bad}", flush=True); time.sleep(10)
            for s in batch:
                ready.put(s if not any(b[0] == s[1] for b in bad) else ("FAIL", s))
        ready.put(None)

    threading.Thread(target=fetcher, daemon=True).start()
    t0 = time.time(); n_done = tot_ok = tot_fail = 0; failed_dl = []
    with ProcessPoolExecutor(a.workers) as ex:
        futs = {}
        while True:
            # thu kết quả đã xong để nhả slot cho fetcher (tránh deadlock khi hàng đợi rỗng)
            for f in [f for f in futs if f.done()]:
                n_done, tot_ok, tot_fail = finish(f, futs.pop(f), out, raw, slots, n_done, tot_ok, tot_fail, len(todo), t0)
            try:
                s = ready.get(timeout=1)
            except queue.Empty:
                continue
            if s is None:
                break
            if s[0] == "FAIL":
                failed_dl.append(s[1][1]); slots.release(); continue
            url, rel, size, sha = s
            dst = out / rel; dst.parent.mkdir(parents=True, exist_ok=True)
            futs[ex.submit(process_shard, str(raw / rel), str(dst), a.size, a.mode, a.quality)] = rel
        for f in as_completed(list(futs)):
            n_done, tot_ok, tot_fail = finish(f, futs.pop(f), out, raw, slots, n_done, tot_ok, tot_fail, len(todo), t0)

    # metadata.parquet từ toàn bộ state
    import pyarrow as pa, pyarrow.parquet as pq
    rows = []
    for st in sorted((out / "_state").glob("*.json")):
        d = json.loads(st.read_text())
        for r in d["rows"]:
            r.update(shard=d["shard"], split=d["split"]); rows.append(r)
    if rows:
        pq.write_table(pa.Table.from_pylist(rows), out / "metadata.parquet", compression="zstd")
    summary = {"source": a.source, "size": a.size, "mode": a.mode, "quality": a.quality,
               "samples": len(rows), "by_split": {}, "failed_download": failed_dl}
    for r in rows:
        summary["by_split"][r["split"]] = summary["by_split"].get(r["split"], 0) + 1
    (out / "_resize_info.json").write_text(json.dumps(summary, indent=2))
    try:
        raw.rmdir()
    except OSError:
        pass
    print("XONG", json.dumps(summary), flush=True)
    sys.exit(1 if failed_dl else 0)


def finish(f, rel, out, raw, slots, n_done, tot_ok, tot_fail, n_todo, t0):
    try:
        ok, fail, rows = f.result()
        split = "validation" if "validation" in rel else ("test" if "test" in rel else "train")
        (out / "_state" / (rel.replace("/", "__") + ".json")).write_text(
            json.dumps({"shard": rel, "split": split, "ok": ok, "fail": fail, "rows": rows}, ensure_ascii=False))
        (raw / rel).unlink(missing_ok=True)
        tot_ok += ok; tot_fail += fail
    except Exception:
        print(f"LỖI xử lý {rel}:\n{traceback.format_exc()}", flush=True)
    slots.release(); n_done += 1
    el = time.time() - t0
    print(f"[{n_done}/{n_todo}] {rel} | {tot_ok} ảnh ok, {tot_fail} lỗi | {tot_ok/el:.0f} ảnh/s | "
          f"ETA {(n_todo-n_done)*el/n_done/60:.0f} phút", flush=True)
    return n_done, tot_ok, tot_fail


if __name__ == "__main__":
    main()
