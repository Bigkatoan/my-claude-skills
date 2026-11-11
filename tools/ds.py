#!/usr/bin/env python3
"""ds - quản lý dataset tập trung tại ~/datasets.

Nguyên tắc: LUÔN tìm trong ~/datasets (và HF cache) trước, chỉ tải khi chưa có.
Dataset tải về luôn nằm trong ~/datasets/<category>/<name>, dự án dùng qua symlink.

  ds list                         liệt kê dataset đã đăng ký
  ds find <query>                 tìm theo tên/alias/tag trong registry, ~/datasets, HF cache
  ds check [name|--all]           kiểm tra tồn tại, dung lượng, file rỗng, symlink hỏng
  ds get <source> -n NAME -c CAT  tải về (nếu chưa có) rồi đăng ký + check
        source: hf:<org>/<repo>[@rev]   (HF dataset; thêm --model nếu là model)
                http(s)://...           (tự giải nén zip/tar*)
                gdrive:<id|url>
  ds link <name> <dest>           tạo symlink dest -> dataset (dùng trong dự án)
  ds register <name> <path> -c CAT [--source S] [--tags a,b] [--desc ...]
  ds scan                         tìm thư mục chưa đăng ký + symlink trỏ vào ~/datasets
"""
import argparse, json, os, shutil, subprocess, sys, tarfile, zipfile, time
from pathlib import Path

ROOT = Path(os.environ.get("DATASETS_ROOT", Path.home() / "datasets"))
REG = ROOT / "registry.json"
HF_HOME = Path(os.environ.get("HF_HOME", Path.home() / ".cache/huggingface"))
SKIP_SCAN = {"_tools", ".venv", "venv", "envs", "node_modules", ".git", "snap", ".cache", "datasets"}


def load():
    return json.loads(REG.read_text()) if REG.exists() else {}


def save(reg):
    REG.write_text(json.dumps(dict(sorted(reg.items())), indent=2, ensure_ascii=False) + "\n")


def du(p: Path):
    try:
        out = subprocess.run(["du", "-sbL", str(p)], capture_output=True, text=True).stdout
        return int(out.split()[0])
    except Exception:
        return 0


def human(n):
    for u in "B KB MB GB TB".split():
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}PB"


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


# ---------------------------------------------------------------- find
def find(query, quiet=False):
    q = norm(query)
    hits = []
    for name, e in load().items():
        keys = [name, *e.get("aliases", []), *e.get("tags", []), e.get("source", "")]
        if any(q in norm(k) or (norm(k) and norm(k) in q) for k in keys):
            hits.append(("registry", name, e["path"]))
    seen = {h[2] for h in hits}
    if ROOT.exists():
        for p in ROOT.glob("*/*"):
            if p.is_dir() and q in norm(p.name) and str(p) not in seen:
                hits.append(("datasets-dir", p.name, str(p)))
    for sub, kind in (("hub", "hf-hub"), ("datasets", "hf-datasets")):
        base = HF_HOME / sub
        if base.exists():
            for p in base.iterdir():
                if p.is_dir() and q in norm(p.name):
                    hits.append((kind, p.name, str(p)))
    if not quiet:
        if not hits:
            print(f"Không tìm thấy '{query}' trong registry, {ROOT} hay HF cache -> có thể tải (ds get).")
        for kind, name, path in hits:
            print(f"[{kind:12}] {name:45} {path}")
    return hits


# ---------------------------------------------------------------- check
def check_path(path: Path, entry=None):
    issues = []
    if not path.exists():
        return {"ok": False, "issues": [f"không tồn tại: {path}"]}
    n_files = n_empty = 0
    exts = {}
    broken = []
    for dp, dns, fns in os.walk(path, followlinks=True):
        for f in fns:
            fp = Path(dp) / f
            if fp.is_symlink() and not fp.exists():
                broken.append(str(fp)); continue
            n_files += 1
            try:
                if fp.stat().st_size == 0 and not f.endswith((".lock", ".flag", ".gitkeep", ".log")) \
                        and not (f.endswith(".txt") and Path(dp).name == "labels"):  # YOLO: ảnh không có object
                    n_empty += 1
            except OSError:
                broken.append(str(fp))
            if ".incomplete" in dp:
                exts[".incomplete"] = exts.get(".incomplete", 0) + 1
            ext = fp.suffix.lower() or "(none)"
            exts[ext] = exts.get(ext, 0) + 1
    size = du(path)
    if n_files == 0:
        issues.append("thư mục rỗng")
    if n_empty:
        issues.append(f"{n_empty} file rỗng (0 byte)")
    if broken:
        issues.append(f"{len(broken)} symlink/file hỏng, vd {broken[0]}")
    if entry:
        exp = entry.get("expected_files")
        if exp and n_files < exp:
            issues.append(f"thiếu file: {n_files}/{exp}")
        # phát hiện tải dở
        for marker in (".incomplete", ".aria2", ".part"):
            if exts.get(marker):
                issues.append(f"{exts[marker]} file tải dở ({marker})")
    top = sorted(exts.items(), key=lambda x: -x[1])[:6]
    return {"ok": not issues, "issues": issues, "files": n_files, "size": size, "exts": top}


def cmd_check(args):
    reg = load()
    names = list(reg) if args.all or not args.name else [args.name]
    bad = 0
    for n in names:
        if n not in reg:
            print(f"'{n}' chưa đăng ký. Gợi ý:"); find(n); bad += 1; continue
        e = reg[n]
        r = check_path(Path(e["path"]), e)
        status = "OK " if r["ok"] else "LỖI"
        extra = f"{r.get('files', 0)} files, {human(r.get('size', 0))}, {r.get('exts', [])}"
        print(f"[{status}] {n:40} {extra}")
        for i in r["issues"]:
            print(f"       - {i}")
        if r.get("size"):
            e.update(size_bytes=r["size"], files=r["files"], checked=time.strftime("%Y-%m-%d"))
        bad += not r["ok"]
    save(reg)
    sys.exit(1 if bad else 0)


# ---------------------------------------------------------------- get
def extract_all(d: Path):
    for f in list(d.iterdir()):
        try:
            if zipfile.is_zipfile(f):
                print(f"giải nén {f.name}"); zipfile.ZipFile(f).extractall(d); f.unlink()
            elif f.is_file() and tarfile.is_tarfile(f):
                print(f"giải nén {f.name}")
                with tarfile.open(f) as t:
                    t.extractall(d, filter="data") if hasattr(tarfile, "data_filter") else t.extractall(d)
                f.unlink()
        except Exception as ex:
            print(f"không giải nén được {f.name}: {ex}")


def cmd_get(args):
    reg = load()
    name, src = args.name, args.source
    dest = ROOT / args.category / name
    # 1) check trước
    if not args.force:
        if name in reg and Path(reg[name]["path"]).exists():
            print(f"Đã có '{name}' tại {reg[name]['path']} -> không tải lại (dùng --force nếu cần).")
            return cmd_check(argparse.Namespace(name=name, all=False))
        same_src = [n for n, e in reg.items() if e.get("source") == src]
        if same_src:
            print(f"Nguồn {src} đã có dưới tên '{same_src[0]}' -> {reg[same_src[0]]['path']}"); return
        hits = find(name.split("/")[-1], quiet=True) + (find(src.split("/")[-1], quiet=True) if ":" in src else [])
        if hits:
            print("Có thể đã có sẵn:")
            for h in hits:
                print(f"  [{h[0]}] {h[1]} -> {h[2]}")
            if not args.yes:
                print("Dừng lại để tránh tải trùng. Dùng --yes để vẫn tải."); sys.exit(2)
    dest.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(ROOT).free
    print(f"Tải {src} -> {dest} (ổ còn trống {human(free)})")
    adl = [sys.executable, str(Path(__file__).resolve().parent / "adl.py")]
    if src.startswith("hf:"):
        cmd = adl + [src, "-d", str(dest)] + (["--model"] if args.model else [])
        for pat in args.include or []:
            cmd += ["--include", pat]
    elif src.startswith(("gdrive:", "http://", "https://", "ftp://")):
        cmd = adl + [src, "-d", str(dest)]
    else:
        sys.exit(f"Nguồn không hỗ trợ: {src}")
    print("$", " ".join(cmd))
    if subprocess.run(cmd).returncode != 0:
        sys.exit("Tải thất bại (file dở vẫn giữ, chạy lại `ds get ... --force` để resume).")
    if not src.startswith("hf:") and not args.no_extract:
        extract_all(dest)
    reg[name] = {**reg.get(name, {}), "path": str(dest), "category": args.category, "source": src,
                 "tags": args.tags.split(",") if args.tags else [], "desc": args.desc or "",
                 "added": time.strftime("%Y-%m-%d")}
    save(reg)
    cmd_check(argparse.Namespace(name=name, all=False))


# ---------------------------------------------------------------- misc
def cmd_list(_):
    reg = load()
    if not reg:
        print("Registry trống."); return
    total = 0
    for n, e in reg.items():
        ok = "✓" if Path(e["path"]).exists() else "✗"
        s = e.get("size_bytes", 0); total += s
        print(f"{ok} {n:38} {e.get('category',''):9} {human(s):>9}  {e.get('desc','')[:60]}")
        for u in e.get("used_by", []):
            print(f"      ↳ {u}")
    print(f"Tổng: {human(total)} | ổ còn trống {human(shutil.disk_usage(ROOT).free)}")


def cmd_link(args):
    reg = load()
    if args.name not in reg:
        sys.exit(f"'{args.name}' chưa đăng ký.")
    dest = Path(args.dest).expanduser().absolute()
    if dest.exists() or dest.is_symlink():
        sys.exit(f"{dest} đã tồn tại - không ghi đè.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.symlink_to(reg[args.name]["path"])
    e = reg[args.name]; e["used_by"] = sorted(set(e.get("used_by", []) + [str(dest)]))
    save(reg); print(f"{dest} -> {e['path']}")


def cmd_register(args):
    reg = load(); p = Path(args.path).expanduser().resolve()
    if not p.exists():
        sys.exit(f"{p} không tồn tại")
    reg[args.name] = {**reg.get(args.name, {}), "path": str(p), "category": args.category,
                      "source": args.source or "", "tags": args.tags.split(",") if args.tags else [],
                      "desc": args.desc or "", "added": time.strftime("%Y-%m-%d")}
    save(reg); cmd_check(argparse.Namespace(name=args.name, all=False))


def cmd_scan(_):
    reg = load(); paths = {e["path"] for e in reg.values()}
    print("== Thư mục trong ~/datasets chưa đăng ký:")
    for p in sorted(ROOT.glob("*/*")):
        if p.is_dir() and p.parent.name != "_tools" and str(p) not in paths:
            print(f"  {p}  ({human(du(p))})")
    print("== Symlink trỏ vào ~/datasets (cập nhật used_by):")
    home = Path.home()
    for dp, dns, fns in os.walk(home):
        dns[:] = [d for d in dns if d not in SKIP_SCAN and not d.startswith(".")]
        if dp.count(os.sep) - str(home).count(os.sep) > 5:
            dns[:] = []
        for f in dns + fns:
            fp = Path(dp) / f
            if fp.is_symlink():
                t = os.path.realpath(fp)
                for n, e in reg.items():
                    if t == e["path"] or t.startswith(e["path"] + os.sep):
                        e["used_by"] = sorted(set(e.get("used_by", []) + [str(fp)]))
                        print(f"  {fp} -> {n}")
    save(reg)


def main():
    ap = argparse.ArgumentParser(prog="ds", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("list").set_defaults(f=cmd_list)
    a = sp.add_parser("find"); a.add_argument("query"); a.set_defaults(f=lambda x: find(x.query))
    a = sp.add_parser("check"); a.add_argument("name", nargs="?"); a.add_argument("--all", action="store_true"); a.set_defaults(f=cmd_check)
    a = sp.add_parser("get"); a.add_argument("source"); a.add_argument("-n", "--name", required=True)
    a.add_argument("-c", "--category", required=True, help="vision|robotics|video|nlp|audio|...")
    a.add_argument("--include", action="append", help="pattern cho hf download (lặp được)")
    a.add_argument("--model", action="store_true"); a.add_argument("--force", action="store_true")
    a.add_argument("--yes", action="store_true", help="vẫn tải dù tìm thấy bản giống")
    a.add_argument("--no-extract", action="store_true"); a.add_argument("--tags"); a.add_argument("--desc")
    a.set_defaults(f=cmd_get)
    a = sp.add_parser("link"); a.add_argument("name"); a.add_argument("dest"); a.set_defaults(f=cmd_link)
    a = sp.add_parser("register"); a.add_argument("name"); a.add_argument("path"); a.add_argument("-c", "--category", required=True)
    a.add_argument("--source"); a.add_argument("--tags"); a.add_argument("--desc"); a.set_defaults(f=cmd_register)
    sp.add_parser("scan").set_defaults(f=cmd_scan)
    args = ap.parse_args(); args.f(args)


if __name__ == "__main__":
    main()
