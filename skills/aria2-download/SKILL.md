---
name: aria2-download
description: Use for ANY file download on this machine - datasets, model weights, checkpoints, archives, HuggingFace repos/files, release assets, single URLs ("tải", "download", "wget", "curl -O", "hf download", "huggingface-cli download", "snapshot_download"). Always download with aria2c via the `adl` wrapper (multi-connection, resume, size/sha256 verification) instead of wget/curl/hf download. Combine with the `datasets` skill when the file is a dataset (check ~/datasets first).
---

# Always download with aria2c (`adl`)

`adl` = `~/datasets/_tools/adl.py` (linked at `~/.local/bin/adl`). It wraps aria2c with: 16 connections per file,
4 files in parallel, automatic resume (`-c`), no overwriting, retries, and a size check after the download (sha256 too with `--verify`).
Running the same command again = resuming whatever is still missing. Exit code != 0 → some files are still bad.

## Commands
```bash
adl URL [URL ...] -d DIR                         # 1 or more URLs
adl -i urls.txt -d DIR                           # list file, one per line: "URL [filename]"
adl hf:org/repo -d DIR [--include 'glob'] [--exclude 'glob'] [--rev REV] [--verify]   # HF dataset repo
adl hf:org/model -d DIR --model                  # HF model repo
adl hf:org/repo --dry-run                        # list files + total size, downloads nothing
adl gdrive:<id|url> -d DIR                       # Drive doesn't support aria2c -> uses gdown
```
- Gated/private HF repos: `adl` reads the token from `HF_TOKEN` or `~/.cache/huggingface/token`. If there is none, ask the user
  to run `! hf auth login` and accept the terms on the web.
- Speed tuning: `-x 16` (connections per file), `-j 8` (parallel files; use more for many small files).
- From Python: `from adl import download, hf_files` (add `~/datasets/_tools` to `sys.path`).

## Rules
1. Before downloading: run `--dry-run` (or HEAD the URL) to get the size, and compare it with `df -h`. If it is >20GB, tell the user the size and the free space first.
2. Datasets → follow the `datasets` skill: `ds find` first, and download into `~/datasets/<category>/<name>`
   (`ds get` already calls `adl`). Model weights for a single project → the project's `ckpt/` or `models/` folder.
3. Large WebDataset that needs resizing or reprocessing (e.g. keeping only 224px images): don't download everything and then process it.
   Use `~/datasets/_tools/wds_resize.py hf:org/repo -o OUT --size 224 --mode crop|stretch|pad` instead. It downloads each shard
   with aria2c, processes it, deletes the original, and resumes on rerun.
4. A failed or partial download: rerun the same command (it resumes). Don't delete `.aria2` files or partial files unless the user agrees.
5. Use wget/curl only when aria2c genuinely can't do it (e.g. you need to POST or stream into a pipe), and say why.
