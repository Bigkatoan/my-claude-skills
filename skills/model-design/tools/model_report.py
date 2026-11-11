#!/usr/bin/env python3
"""model_report - đo nhanh một nn.Module trước khi đem đi train.

  python model_report.py path/to/model.py:build_model --input 8,3,224,224
  python model_report.py model.py:VAE --kwargs '{"z_dim": 16}' --input 4,3,256,256 --bf16
  python model_report.py model.py:Net --input 2,77:long --input 2,3,224,224      # nhiều input, dtype riêng
  python model_report.py timm:resnet50 --input 32,3,224,224 --bf16               # baseline từ timm

In ra: params (tổng, trainable, theo module con), shape output, FLOPs (fwd), VRAM đỉnh và thời gian
fwd+bwd, throughput, và kiểm tra gradient: param không nhận grad (unused), grad = 0, NaN/Inf.
Output được coi là loss nếu là scalar; nếu không, loss giả = sum(mean(o * r)) với r ngẫu nhiên cố định
(tránh mean(o) - BatchNorm/LayerNorm triệt tiêu gradient của loss dạng trung bình -> báo nhầm grad = 0).
"""
import argparse, importlib.util, json, sys, time
from pathlib import Path

import torch
import torch.nn as nn


def load(spec, kwargs):
    src, _, name = spec.rpartition(":")
    if src == "timm":
        import timm
        return timm.create_model(name, **kwargs)
    p = Path(src).resolve(); sys.path.insert(0, str(p.parent))
    m = importlib.util.spec_from_file_location(p.stem, p); mod = importlib.util.module_from_spec(m); m.loader.exec_module(mod)
    obj = getattr(mod, name)
    return obj(**kwargs)


def parse_input(s, dev):
    shape, _, dt = s.partition(":")
    shape = [int(x) for x in shape.split(",")]
    if dt in ("long", "int"):
        return torch.randint(0, 100, shape, device=dev)
    return torch.randn(shape, device=dev)


def tensors(o):
    if torch.is_tensor(o):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from tensors(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from tensors(v)


def human(n, unit=""):
    for u in ["", "K", "M", "G", "T"]:
        if abs(n) < 1000:
            return f"{n:.2f}{u}{unit}"
        n /= 1000
    return f"{n:.2f}P{unit}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="file.py:callable  hoặc  timm:model_name")
    ap.add_argument("--kwargs", default="{}"); ap.add_argument("--input", action="append", required=True)
    ap.add_argument("--bf16", action="store_true"); ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--iters", type=int, default=10); ap.add_argument("--depth", type=int, default=1, help="độ sâu bảng params")
    a = ap.parse_args()
    dev = torch.device("cpu" if a.cpu or not torch.cuda.is_available() else "cuda")
    model = load(a.spec, json.loads(a.kwargs)).to(dev).train()
    xs = [parse_input(s, dev) for s in a.input]
    amp = torch.autocast(dev.type, dtype=torch.bfloat16, enabled=a.bf16)

    # ---- params
    tot = sum(p.numel() for p in model.parameters()); tr = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"== {a.spec}  params {human(tot)} (trainable {human(tr)}), fp32 weights {tot*4/2**20:.1f} MiB")
    rows = {}
    for n, p in model.named_parameters():
        k = ".".join(n.split(".")[:a.depth]); rows[k] = rows.get(k, 0) + p.numel()
    for k, v in sorted(rows.items(), key=lambda x: -x[1])[:25]:
        print(f"   {k:40} {human(v):>9}  {100*v/max(tot,1):5.1f}%")

    # ---- forward: shapes + FLOPs
    from torch.utils.flop_counter import FlopCounterMode
    with torch.no_grad(), amp:
        fc = FlopCounterMode(display=False)
        with fc:
            out = model(*xs)
    print("== output:", [tuple(t.shape) for t in tensors(out)], [str(t.dtype) for t in tensors(out)][:4])
    fl = fc.get_total_flops()
    print(f"== FLOPs fwd {human(fl)}  (~{human(fl/ xs[0].shape[0])}/sample; fwd+bwd ≈ 3x)")

    # ---- grads
    model.zero_grad(set_to_none=True)
    with amp:
        out = model(*xs)
    ts = list(tensors(out))
    g = torch.Generator(device=dev).manual_seed(0)
    proj = [torch.randn(t.shape, generator=g, device=dev) for t in ts]
    fake = lambda ts: sum((t.float() * r).mean() for t, r in zip(ts, proj) if t.is_floating_point())
    loss = ts[0] if len(ts) == 1 and ts[0].ndim == 0 else fake(ts)
    loss.backward()
    none = [n for n, p in model.named_parameters() if p.requires_grad and p.grad is None]
    zero = [n for n, p in model.named_parameters() if p.grad is not None and p.grad.abs().max() == 0]
    bad = [n for n, p in model.named_parameters() if p.grad is not None and not torch.isfinite(p.grad).all()]
    print(f"== loss {loss.item():.4g} | grad: unused={len(none)} zero={len(zero)} nonfinite={len(bad)}")
    for lbl, l in (("unused", none), ("zero", zero), ("nonfinite", bad)):
        for n in l[:8]:
            print(f"   {lbl}: {n}")
    if zero:
        z0 = [n for n, p in model.named_parameters() if p.ndim == 1 and p.abs().max() == 0 and "bias" not in n]
        print(f"   gợi ý: grad=0 thường do một tham số phía sau đang khởi tạo bằng 0 (zero-init residual/gate)."
              f" Tham số đang = 0: {z0[:4]}{' ...' if len(z0) > 4 else ''} -> bình thường ở bước 0 nếu cố ý.")
    if any(not torch.isfinite(t).all() for t in ts):
        print("   !! output có NaN/Inf")

    # ---- speed + memory (fwd+bwd)
    if dev.type == "cuda":
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
        base = torch.cuda.memory_allocated()
        for i in range(a.iters + 3):
            if i == 3:
                torch.cuda.synchronize(); t0 = time.time()
            model.zero_grad(set_to_none=True)
            with amp:
                out = model(*xs)
            o = list(tensors(out)); (o[0] if len(o) == 1 and o[0].ndim == 0 else fake(o)).backward()
        torch.cuda.synchronize(); dt = (time.time() - t0) / a.iters
        peak = torch.cuda.max_memory_allocated()
        tot_mem = torch.cuda.get_device_properties(0).total_memory
        print(f"== fwd+bwd {dt*1e3:.1f} ms/iter, {xs[0].shape[0]/dt:.0f} samples/s, "
              f"VRAM đỉnh {peak/2**30:.2f} GiB (activations ~{(peak-base)/2**30:.2f}) / {tot_mem/2**30:.1f} GiB "
              f"[{'bf16' if a.bf16 else 'fp32'}; chưa tính optimizer state AdamW = 2x params fp32 = {tot*8/2**30:.2f} GiB]")
        print(f"   ước lượng batch tối đa (tuyến tính theo activations): "
              f"~{int(xs[0].shape[0] * (tot_mem*0.9 - base - tot*8) / max(peak-base,1))}")


if __name__ == "__main__":
    main()
