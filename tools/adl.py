#!/usr/bin/env python3
"""adl - tải nhanh bằng aria2c (đa kết nối, resume, kiểm tra kích thước/sha256).

  adl URL [URL ...] [-d DIR]                 tải 1 hay nhiều URL
  adl -i urls.txt -d DIR                     tải theo danh sách (mỗi dòng: URL [tên_file])
  adl hf:org/repo -d DIR [--include GLOB]... HF dataset repo (thêm --model cho model repo)
        [--exclude GLOB] [--rev REV] [--verify]
  adl gdrive:<id|url> -d DIR                 Google Drive (aria2c không hỗ trợ -> dùng gdown)

Mặc định: -x16 -s16 kết nối/file, -j4 file song song, tự resume (-c), không ghi đè.
Chạy lại cùng lệnh = tải tiếp phần còn thiếu. Exit code != 0 nếu còn file lỗi.
"""
import argparse, fnmatch, hashlib, os, shutil, subprocess, sys, tempfile
from pathlib import Path


def human(n):
    for u in "B KB MB GB TB".split():
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"


def hf_token():
    t = os.environ.get("HF_TOKEN")
    p = Path(os.environ.get("HF_HOME", Path.home() / ".cache/huggingface")) / "token"
    return t or (p.read_text().strip() if p.exists() else None)


def hf_files(repo, repo_type, rev, include, exclude):
    """-> list of (url, relpath, size, sha256|None), needs_auth"""
    from huggingface_hub import HfApi
    api = HfApi(token=hf_token())
    info = (api.model_info if repo_type == "model" else api.dataset_info)(repo, revision=rev, files_metadata=True)
    base = "https://huggingface.co/" + ("" if repo_type == "model" else "datasets/") + repo
    out = []
    for s in info.siblings:
        f = s.rfilename
        if include and not any(fnmatch.fnmatch(f, g) for g in include):
            continue
        if exclude and any(fnmatch.fnmatch(f, g) for g in exclude):
            continue
        sha = s.lfs.sha256 if getattr(s, "lfs", None) else None
        out.append((f"{base}/resolve/{rev or 'main'}/{f}", f, s.size, sha))
    return out, bool(info.gated or info.private)


def sha256(p, bs=1 << 22):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(bs):
            h.update(b)
    return h.hexdigest()


def download(items, dest, headers=(), conns=16, jobs=4, quiet=False):
    """items: list of (url, relpath, size|None, sha|None). Trả về list file lỗi."""
    dest = Path(dest); dest.mkdir(parents=True, exist_ok=True)
    todo = []
    for url, rel, size, sha in items:
        p = dest / rel
        done = p.exists() and not Path(str(p) + ".aria2").exists() and (size is None or p.stat().st_size == size)
        if not done:
            todo.append((url, rel, size, sha))
    need = sum(s or 0 for _, _, s, _ in todo)
    free = shutil.disk_usage(dest).free
    if not quiet:
        print(f"{len(items)} file, cần tải {len(todo)} ({human(need)}), ổ còn trống {human(free)} -> {dest}")
    if need > free:
        sys.exit("Không đủ dung lượng.")
    if todo:
        with tempfile.NamedTemporaryFile("w", suffix=".aria2in", delete=False) as fh:
            for url, rel, *_ in todo:
                fh.write(f"{url}\n  out={rel}\n")
                for h in headers:
                    fh.write(f"  header={h}\n")
            inp = fh.name
        cmd = ["aria2c", "-i", inp, "-d", str(dest), "-c", f"-x{conns}", f"-s{conns}", f"-j{jobs}", "-k1M",
               "--file-allocation=none", "--auto-file-renaming=false", "--allow-overwrite=false",
               "--max-tries=10", "--retry-wait=5", "--timeout=60", "--console-log-level=warn",
               "--summary-interval=0" if quiet else "--summary-interval=30", "--download-result=hide" if quiet else "--download-result=default"]
        if quiet:
            cmd.append("-q")
        subprocess.run(cmd)
        os.unlink(inp)
    bad = []
    for url, rel, size, sha in items:
        p = dest / rel
        if not p.exists() or Path(str(p) + ".aria2").exists():
            bad.append((rel, "thiếu/tải dở"))
        elif size is not None and p.stat().st_size != size:
            bad.append((rel, f"sai kích thước {p.stat().st_size} != {size}"))
    return bad


def main():
    ap = argparse.ArgumentParser(prog="adl", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="*")
    ap.add_argument("-d", "--dir", default=".")
    ap.add_argument("-i", "--input", help="file danh sách URL")
    ap.add_argument("-x", "--conns", type=int, default=16)
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("--include", action="append"); ap.add_argument("--exclude", action="append")
    ap.add_argument("--rev"); ap.add_argument("--model", action="store_true")
    ap.add_argument("--verify", action="store_true", help="kiểm tra sha256 (file LFS trên HF)")
    ap.add_argument("--header", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    items, headers = [], list(a.header)
    srcs = list(a.sources)
    if a.input:
        for line in Path(a.input).read_text().splitlines():
            if line.strip() and not line.startswith("#"):
                srcs.append(line.strip())
    if not srcs:
        ap.error("cần ít nhất 1 nguồn")
    for s in srcs:
        if s.startswith("hf:"):
            repo, _, rev = s[3:].partition("@")
            files, auth = hf_files(repo, "model" if a.model else "dataset", rev or a.rev, a.include, a.exclude)
            items += files
            if auth or hf_token():
                tok = hf_token()
                if auth and not tok:
                    sys.exit(f"{repo} là repo gated/private: chạy `hf auth login` và chấp nhận điều khoản trên web.")
                if auth:
                    headers.append(f"Authorization: Bearer {tok}")
        elif s.startswith("gdrive:"):
            sys.exit(subprocess.run(["gdown", "--fuzzy", s[7:], "-O", a.dir.rstrip("/") + "/"]).returncode)
        else:
            url, *name = s.split()
            items.append((url, name[0] if name else url.split("?")[0].rstrip("/").split("/")[-1], None, None))
    if a.dry_run:
        for u, r, sz, _ in items:
            print(f"{human(sz or 0):>9}  {r}")
        print(f"Tổng {len(items)} file, {human(sum(i[2] or 0 for i in items))}"); return
    bad = download(items, a.dir, headers, a.conns, a.jobs)
    if a.verify:
        for u, rel, sz, sha in items:
            p = Path(a.dir) / rel
            if sha and p.exists() and sha256(p) != sha:
                bad.append((rel, "sai sha256"))
    for rel, why in bad:
        print(f"LỖI {rel}: {why}")
    print("Xong, tất cả OK." if not bad else f"{len(bad)} file lỗi - chạy lại lệnh để tải tiếp.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
