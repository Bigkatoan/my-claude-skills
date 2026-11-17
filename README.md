# my-claude-skills

Bộ [skill](https://docs.claude.com/en/docs/claude-code/skills) cá nhân cho Claude Code, kèm công cụ dòng lệnh đi cùng.

| Skill | Dùng khi | Công cụ |
|---|---|---|
| [`datasets`](skills/datasets/SKILL.md) | Cần dataset: tìm, kiểm tra, tải, gắn vào dự án. Mọi dataset nằm **một bản** trong `~/datasets`, dự án dùng qua symlink. | `ds` |
| [`aria2-download`](skills/aria2-download/SKILL.md) | Bất kỳ lần tải nào (URL, HuggingFace, Drive) → luôn dùng aria2c: đa kết nối, resume, kiểm tra size/sha256. | `adl`, `wds_resize.py` |
| [`pytorch-training`](skills/pytorch-training/SKILL.md) | Train / fine-tune / debug training PyTorch: template `train.py` một file (bf16, accum, EMA, compile, resume, NaN guard), sanity ladder, chẩn đoán NaN/OOM/chậm, chạy job dài + monitor. | `templates/train.py` |
| [`model-design`](skills/model-design/SKILL.md) | Thiết kế / review kiến trúc: spec → baseline → đo → test → ablation; quy ước code, ước lượng params/FLOPs/VRAM cho 12GB, block có sẵn (ConvNeXt, ResBlock-AdaGN, SDPA+RoPE, DiT adaLN-zero, VAE posterior, VQ). | `tools/model_report.py`, `blocks.py` |
| [`manim-visualize`](skills/manim-visualize/SKILL.md) | "visualize / minh hoạ": video Manim, ưu tiên hình, gần như không chữ. | `reference.py` |
| [`hibiscus-design`](skills/hibiscus-design/SKILL.md) | Dự án dùng giao diện Hibiscus (letrain, Robot Ops…): lấy asset, linh vật Hibi, animation, màu sáng/tối từ repo `hibiscus-assets`, không vẽ/copy lẻ. | `hibiscus-assets/tools/sync.sh` |
| [`company`](skills/company/SKILL.md) | Giao việc lớn cho "cả công ty" agent: đủ role lãnh đạo, sản phẩm (PM, BA, UX/UI, CX, nội dung), kỹ thuật (architect, backend, frontend, data/ML, integrator, DevOps), chất lượng (QA, QC, bảo mật, hiệu năng, a11y), kinh doanh (marketing/SEO, sales, CSKH, pháp lý, tài chính, vận hành), tài liệu/release. Coi bạn là khách hàng: BA làm rõ yêu cầu theo vòng Khách hàng → BA → Tech Lead + SA → BA → Khách hàng cho tới khi bạn duyệt (BRD, SRS, tài liệu kiến trúc, tài liệu nghiệm thu, danh sách tính năng, danh sách tính năng đã duyệt). QC test từng tính năng, tính năng không đạt thì không lên sản phẩm. Có người điều phối báo cáo tiến độ liên tục (đang làm gì, đến đâu, bao lâu nữa xong). Có playbook theo loại việc, mẫu brief, QC checklist, bảng trạng thái, khung workflow. | `requirements.md`, `templates/`, `playbooks.md` |

## Cài đặt
```bash
git clone https://github.com/Bigkatoan/my-claude-skills.git
cd my-claude-skills
./install.sh          # copy vào ~/.claude/skills và ~/datasets/_tools
./install.sh --link   # hoặc symlink: sửa trong repo là có hiệu lực luôn
```
Yêu cầu: `python3` ≥ 3.8, `aria2c` (`sudo apt install aria2`), `pip install huggingface_hub pyarrow pillow`; `gdown` nếu tải từ Google Drive; `manim` cho skill visualize.

## Công cụ

### `ds` — quản lý dataset tập trung
```bash
ds find coco                              # tìm trong registry, ~/datasets và HF cache
ds get hf:org/repo -n name -c vision      # chỉ tải khi chưa có (qua adl), tự đăng ký + check
ds check --all                            # file rỗng, symlink hỏng, file tải dở
ds link name ~/Project/data/name          # symlink vào dự án
ds register name path -c vision           # đăng ký dữ liệu có sẵn
ds scan                                   # tìm thư mục chưa đăng ký, cập nhật used_by
```
Cấu trúc: `~/datasets/<category>/<name>` + `~/datasets/registry.json`. Đổi gốc bằng biến `DATASETS_ROOT`.

### `adl` — tải bằng aria2c
```bash
adl URL [URL...] -d DIR                   # 16 kết nối/file, 4 file song song, resume
adl -i urls.txt -d DIR
adl hf:org/repo -d DIR --include '*.tar' [--verify]   # repo HF, tự dùng token với repo gated
adl hf:org/repo --dry-run                 # xem dung lượng trước
```

### `wds_resize.py` — tải & resize WebDataset theo luồng
Tải từng shard bằng aria2c → resize → xoá shard gốc, nên không cần chứa cả bộ gốc. Chạy lại = tiếp tục.
```bash
python3 wds_resize.py hf:pixparse/cc3m-wds -o ~/datasets/vision/cc3m_224 --size 224 --mode stretch
```
Giữ caption (`.txt`) và metadata gốc (`.json`), ghi thêm `metadata.parquet`. `--mode stretch` (mặc định, resize thẳng, giữ toàn bộ nội dung) | `crop` | `pad`.

### `model_report.py` — đo model trước khi train
```bash
python model_report.py model.py:build_model --kwargs '{"dim":256}' --input 16,3,224,224 --bf16
python model_report.py timm:resnet50 --input 32,3,224,224 --bf16
```
Params theo module, shape output, FLOPs, VRAM đỉnh fwd+bwd, throughput, batch tối đa ước lượng, param không nhận grad / grad = 0 / NaN.

## License
MIT
