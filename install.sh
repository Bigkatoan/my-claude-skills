#!/usr/bin/env bash
# Cài skills vào ~/.claude/skills và tools vào ~/datasets/_tools (+ lệnh ds, adl trong ~/.local/bin).
#   ./install.sh          copy (mặc định)
#   ./install.sh --link   symlink về repo này -> sửa trong repo là có hiệu lực ngay
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-copy}"
SKILLS="$HOME/.claude/skills"; TOOLS="${DATASETS_ROOT:-$HOME/datasets}/_tools"; BIN="$HOME/.local/bin"
mkdir -p "$SKILLS" "$TOOLS" "$BIN"

put() {  # put SRC DST
  local src="$1" dst="$2"
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    mv "$dst" "$dst.bak.$(date +%s)"; echo "  backup $dst"
  fi
  if [ "$MODE" = "--link" ]; then ln -s "$src" "$dst"; else cp -r "$src" "$dst"; fi
  echo "  $dst"
}

echo "Skills -> $SKILLS"
for d in "$REPO"/skills/*/; do put "${d%/}" "$SKILLS/$(basename "$d")"; done
echo "Tools -> $TOOLS"
for f in "$REPO"/tools/*.py; do put "$f" "$TOOLS/$(basename "$f")"; done
ln -sf "$TOOLS/ds.py" "$BIN/ds"; ln -sf "$TOOLS/adl.py" "$BIN/adl"
[ -f "${DATASETS_ROOT:-$HOME/datasets}/registry.json" ] || echo '{}' > "${DATASETS_ROOT:-$HOME/datasets}/registry.json"

for c in aria2c python3; do command -v $c >/dev/null || echo "CẢNH BÁO: thiếu $c (sudo apt install aria2 / python3)"; done
python3 -c "import huggingface_hub" 2>/dev/null || echo "Gợi ý: pip install --user huggingface_hub pyarrow pillow"
case ":$PATH:" in *":$BIN:"*) ;; *) echo "Thêm $BIN vào PATH để dùng lệnh ds/adl";; esac
echo "Xong. Mở phiên Claude Code mới để skill có hiệu lực."
