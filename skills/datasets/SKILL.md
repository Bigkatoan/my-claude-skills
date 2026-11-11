---
name: datasets
description: Use whenever a task needs a dataset (or a large pretrained model/data file) - downloading, locating, preparing, checking or pointing a project at data, e.g. "tải dataset", "download COCO/ImageNet/LeRobot/HF dataset", "data ở đâu", "check data", "dataset bị thiếu/hỏng", or when writing a data loader/config that needs a data path. Always look in ~/datasets first; only download when it is genuinely missing, and download into ~/datasets, never into a project folder.
---

# Datasets live in `~/datasets` — check first, download second

Every dataset on this machine is stored once in `~/datasets/<category>/<name>` and catalogued in
`~/datasets/registry.json`. Projects use the data through **symlinks**, never through their own copies.
The CLI is `ds` (`~/datasets/_tools/ds.py`, linked at `~/.local/bin/ds`). Run `ds -h` for the full set of options.

Categories: `vision`, `robotics`, `video`, `nlp`, `audio`, `tabular`, `misc` (add a new one only if none fits).

## Workflow (do it in this order)

1. **Search first** — before any download or any hard-coded path:
   ```bash
   ds find <keyword>      # searches the registry (name/alias/tag/source), ~/datasets, and the HF cache
   ds list                # full catalogue + size + which projects use each dataset
   ```
   Try several keywords (`coco`, `coco2017`, `mscoco`). If anything turns up, use it. Don't download again.

2. **Check** whatever you are about to use:
   ```bash
   ds check <name>        # exists, size, file count, 0-byte files, broken symlinks, partial downloads
   ds check --all
   ```
   If the result says LỖI, report it to the user. Never delete partial data without asking: `.part`/`.incomplete`
   files can be resumed (`ds get ... --force` resumes for aria2c/wget/hf).

3. **Download only if it is missing**:
   ```bash
   ds get hf:<org>/<repo>[@rev] -n <name> -c <category> [--include "pattern/*"] [--tags a,b] [--desc "..."]
   ds get hf:<org>/<model> -n <name> -c models --model     # HF model (if it really needs its own copy)
   ds get https://.../file.zip -n <name> -c <category>      # aria2c 8 connections, auto-extracts zip/tar
   ds get gdrive:<id-or-url> -n <name> -c <category>
   ```
   `ds get` checks the registry and the HF cache on its own and stops (exit 2) if it finds something similar.
   Only add `--yes` once you have confirmed that it really is a different dataset.
   Before a large download (>20GB), tell the user the size and how much disk is free (`df -h /`).
   After the download, `ds get` registers the dataset and runs `check` automatically.

4. **Attach it to the project** with a symlink. Don't copy and don't hard-code an absolute path in code when you can avoid it:
   ```bash
   ds link <name> <project>/data/<name>
   ```
   In config/code, use the path `<project>/data/<name>` or the env var `DATASETS_ROOT` (default `~/datasets`).

5. **Data that already exists but isn't registered** (e.g. the user copied it in by hand):
   move it into `~/datasets/<category>/<name>` (`mv` on the same disk is instant), put a symlink back at the old location,
   then `ds register <name> <path> -c <category> --tags ... --desc ...` and `ds scan` (updates `used_by`).

## Rules
- Don't create dataset copies inside project folders, and don't extract datasets into `/tmp` or the scratchpad.
- Derived data (features, cache, splits, preprocessed outputs) that belongs to one project stays in that project.
  Only raw or reusable data goes into `~/datasets`.
- HF datasets loaded with `load_dataset` stay in the `~/.cache/huggingface` cache. `ds find` searches there too;
  register the ones you use often with `ds register`.
- `libero_assets` stays in `~/.cache/libero` because LIBERO hard-codes that path.
- Never delete anything in `~/datasets` unless the user explicitly asks.
