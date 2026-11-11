#!/usr/bin/env python3
"""Single-file PyTorch training template (plain PyTorch, no framework).

Copy to <project>/train.py, then fill in the 3 hooks marked  >>> HOOK:
    build_model(a) -> nn.Module
    build_data(a)  -> (train_loader, val_loader | None)
    compute_loss(model, batch, a) -> (loss, {metric: float})
Everything else (bf16 autocast, grad accum, clipping, AdamW + no-decay groups, warmup+cosine,
EMA, torch.compile, checkpoint/resume, eval, jsonl/tensorboard/wandb logging, throughput, VRAM) is generic.

  python train.py --demo --steps 200                      # smoke test with synthetic data
  python train.py --name exp1 --steps 50000 --bs 128 --lr 3e-4
  python train.py --name exp1 --resume                    # continue runs/exp1/last.pt
  python train.py --demo --overfit 1 --steps 300          # sanity: must drive loss ~0 on one batch
"""
import argparse, contextlib, copy, json, math, os, random, sys, time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================================ >>> HOOK 1: model
def build_model(a):
    if a.demo:
        return nn.Sequential(nn.Conv2d(3, 32, 3, 2, 1), nn.GroupNorm(8, 32), nn.GELU(),
                             nn.Conv2d(32, 64, 3, 2, 1), nn.GroupNorm(8, 64), nn.GELU(),
                             nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(64, 10))
    raise NotImplementedError("build_model: return your nn.Module")


# ============================================================================ >>> HOOK 2: data
def build_data(a):
    """Return (train_loader, val_loader|None). Data lives in ~/datasets (see `datasets` skill):
    e.g. webdataset: wds.WebDataset(f"{DATA}/cc3m-train-{{0000..0575}}.tar", shardshuffle=True)..."""
    if a.demo:
        g = torch.Generator().manual_seed(0)
        x = torch.randn(2048, 3, 32, 32, generator=g); y = torch.randint(0, 10, (2048,), generator=g)
        x[torch.arange(2048), y % 3, :4, :4] += 3.0  # learnable signal
        ds = torch.utils.data.TensorDataset(x, y)
        tr, va = torch.utils.data.random_split(ds, [1792, 256], generator=g)
        mk = lambda d, sh: torch.utils.data.DataLoader(d, batch_size=a.bs, shuffle=sh, drop_last=sh,
                                                        num_workers=0, pin_memory=True)
        return mk(tr, True), mk(va, False)
    raise NotImplementedError("build_data: return (train_loader, val_loader)")


# ============================================================================ >>> HOOK 3: loss
def compute_loss(model, batch, a):
    """Return (scalar loss, dict of float metrics). Runs inside autocast."""
    x, y = batch
    logits = model(x)
    loss = F.cross_entropy(logits.float(), y)
    return loss, {"acc": (logits.argmax(-1) == y).float().mean().item()}


# ============================================================================ generic machinery
def get_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="debug"); ap.add_argument("--out", default="runs")
    ap.add_argument("--config", help="json/yaml file whose keys override the defaults below")
    ap.add_argument("--demo", action="store_true", help="synthetic data + tiny model (smoke test)")
    # optimisation
    ap.add_argument("--steps", type=int, default=10000); ap.add_argument("--bs", type=int, default=64)
    ap.add_argument("--accum", type=int, default=1, help="grad accumulation; effective bs = bs*accum")
    ap.add_argument("--lr", type=float, default=3e-4); ap.add_argument("--min_lr_ratio", type=float, default=0.1)
    ap.add_argument("--warmup", type=int, default=500); ap.add_argument("--wd", type=float, default=0.05)
    ap.add_argument("--betas", type=float, nargs=2, default=(0.9, 0.95)); ap.add_argument("--clip", type=float, default=1.0)
    ap.add_argument("--ema", type=float, default=0.0, help="EMA decay, e.g. 0.999 (0 = off)")
    # numerics / speed
    ap.add_argument("--precision", choices=["bf16", "fp16", "fp32"], default="bf16")
    ap.add_argument("--compile", action="store_true"); ap.add_argument("--channels_last", action="store_true")
    ap.add_argument("--workers", type=int, default=8); ap.add_argument("--seed", type=int, default=0)
    # bookkeeping
    ap.add_argument("--log_every", type=int, default=50); ap.add_argument("--eval_every", type=int, default=1000)
    ap.add_argument("--save_every", type=int, default=1000); ap.add_argument("--eval_batches", type=int, default=50)
    ap.add_argument("--resume", action="store_true"); ap.add_argument("--init", help="load weights only (finetune)")
    ap.add_argument("--wandb", action="store_true"); ap.add_argument("--tb", action="store_true")
    ap.add_argument("--overfit", type=int, default=0, help="train on N fixed batches only (sanity check)")
    a = ap.parse_args(argv)
    if a.config:
        txt = Path(a.config).read_text()
        cfg = json.loads(txt) if a.config.endswith(".json") else __import__("yaml").safe_load(txt)
        for k, v in cfg.items():
            if not hasattr(a, k):
                sys.exit(f"unknown config key: {k}")
            setattr(a, k, v)
        a = ap.parse_args(argv, namespace=a)  # CLI flags still win over the config file
    return a


def seed_all(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s); torch.cuda.manual_seed_all(s)


def param_groups(model, wd):
    """No weight decay on biases, norm weights, embeddings-like 1-D params."""
    decay, no = [], []
    for n, p in model.named_parameters():
        if not p.requires_grad:
            continue
        (no if p.ndim < 2 or n.endswith(".bias") or "norm" in n.lower() or "embed" in n.lower() else decay).append(p)
    return [{"params": decay, "weight_decay": wd}, {"params": no, "weight_decay": 0.0}]


def lr_at(step, a):
    if step < a.warmup:
        return a.lr * (step + 1) / a.warmup
    t = min(1.0, (step - a.warmup) / max(1, a.steps - a.warmup))
    return a.lr * (a.min_lr_ratio + (1 - a.min_lr_ratio) * 0.5 * (1 + math.cos(math.pi * t)))


def to_device(b, dev, cl=False):
    if torch.is_tensor(b):
        b = b.to(dev, non_blocking=True)
        return b.contiguous(memory_format=torch.channels_last) if cl and b.ndim == 4 and b.is_floating_point() else b
    if isinstance(b, (list, tuple)):
        return type(b)(to_device(x, dev, cl) for x in b)
    if isinstance(b, dict):
        return {k: to_device(v, dev, cl) for k, v in b.items()}
    return b


def infinite(loader):
    ep = 0
    while True:
        if hasattr(loader, "sampler") and hasattr(loader.sampler, "set_epoch"):
            loader.sampler.set_epoch(ep)
        for b in loader:
            yield b
        ep += 1


class Logger:
    def __init__(self, run, a):
        self.f = open(run / "log.jsonl", "a"); self.tb = self.wb = None
        if a.tb:
            from torch.utils.tensorboard import SummaryWriter
            self.tb = SummaryWriter(run / "tb")
        if a.wandb:
            import wandb
            self.wb = wandb.init(project=Path.cwd().name, name=a.name, config=vars(a), dir=str(run), resume="allow")

    def __call__(self, step, d):
        d = {"step": step, **{k: (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()}}
        self.f.write(json.dumps(d) + "\n"); self.f.flush()
        if self.tb:
            for k, v in d.items():
                if isinstance(v, (int, float)) and k != "step":
                    self.tb.add_scalar(k, v, step)
        if self.wb:
            self.wb.log(d, step=step)


@torch.no_grad()
def evaluate(model, loader, a, dev, amp):
    if loader is None:
        return {}
    model.eval(); tot, n = {}, 0
    for i, b in enumerate(loader):
        if i >= a.eval_batches:
            break
        with amp():
            loss, m = compute_loss(model, to_device(b, dev, a.channels_last), a)
        for k, v in {"loss": loss.item(), **m}.items():
            tot[k] = tot.get(k, 0.0) + v
        n += 1
    model.train()
    return {f"val/{k}": v / max(n, 1) for k, v in tot.items()}


def save(path, **state):
    tmp = Path(str(path) + ".tmp"); torch.save(state, tmp); os.replace(tmp, path)  # atomic: no half-written ckpt


def main(a):
    run = Path(a.out) / a.name; run.mkdir(parents=True, exist_ok=True)
    seed_all(a.seed)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.backends.cuda.matmul.allow_tf32 = True; torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True
    dt = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": None}[a.precision]
    amp = (lambda: torch.autocast(dev.type, dtype=dt)) if dt else contextlib.nullcontext
    scaler = torch.amp.GradScaler(enabled=a.precision == "fp16")

    model = build_model(a).to(dev)
    if a.channels_last:
        model = model.to(memory_format=torch.channels_last)
    if a.init:
        sd = torch.load(a.init, map_location="cpu"); sd = sd.get("ema") or sd.get("model") or sd
        print("init:", model.load_state_dict(sd, strict=False))
    n_par = sum(p.numel() for p in model.parameters()); n_tr = sum(p.numel() for p in model.parameters() if p.requires_grad)
    ema = copy.deepcopy(model).eval().requires_grad_(False) if a.ema > 0 else None
    opt = torch.optim.AdamW(param_groups(model, a.wd), lr=a.lr, betas=tuple(a.betas), fused=dev.type == "cuda")
    fwd_model = torch.compile(model) if a.compile else model

    step = 0
    if a.resume and (run / "last.pt").exists():
        ck = torch.load(run / "last.pt", map_location="cpu", weights_only=False)
        model.load_state_dict(ck["model"]); opt.load_state_dict(ck["opt"]); scaler.load_state_dict(ck["scaler"])
        if ema is not None and ck.get("ema"):
            ema.load_state_dict(ck["ema"])
        step = ck["step"]; random.setstate(ck["rng"]["py"]); np.random.set_state(ck["rng"]["np"]); torch.set_rng_state(ck["rng"]["torch"])
        print(f"resumed from step {step}")
    (run / "args.json").write_text(json.dumps(vars(a), indent=2))

    train_loader, val_loader = build_data(a)
    it = infinite(train_loader)
    if a.overfit:
        fixed = [next(it) for _ in range(a.overfit)]; it = (fixed[i % a.overfit] for i in range(10 ** 12))
    log = Logger(run, a)
    print(f"run={run} params={n_par/1e6:.2f}M trainable={n_tr/1e6:.2f}M eff_bs={a.bs*a.accum} dev={dev} {a.precision}")

    model.train(); t0 = time.time(); seen = 0; best = float("inf"); acc_m = {}
    while step < a.steps:
        for g in opt.param_groups:
            g["lr"] = lr_at(step, a)
        for micro in range(a.accum):
            b = to_device(next(it), dev, a.channels_last)
            with amp():
                loss, m = compute_loss(fwd_model, b, a)
            if not torch.isfinite(loss):
                save(run / "nan_batch.pt", batch=b, step=step)
                sys.exit(f"non-finite loss at step {step}; batch saved to {run/'nan_batch.pt'}")
            scaler.scale(loss / a.accum).backward()
            for k, v in {"loss": loss.item(), **m}.items():
                acc_m[k] = acc_m.get(k, 0.0) + v / a.accum
            seen += (b[0] if isinstance(b, (list, tuple)) else next(iter(b.values())) if isinstance(b, dict) else b).shape[0]
        scaler.unscale_(opt)
        gn = torch.nn.utils.clip_grad_norm_(model.parameters(), a.clip if a.clip > 0 else float("inf"))
        scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True)
        if ema is not None:
            with torch.no_grad():
                d = min(a.ema, (1 + step) / (10 + step))  # warm EMA early
                for pe, pm in zip(ema.parameters(), model.parameters()):
                    pe.lerp_(pm.detach(), 1 - d)
                for be, bm in zip(ema.buffers(), model.buffers()):
                    be.copy_(bm)
        step += 1

        if step % a.log_every == 0 or step == 1:
            el = time.time() - t0
            rec = {k: v / (1 if step == 1 else a.log_every) for k, v in acc_m.items()}
            rec.update(lr=opt.param_groups[0]["lr"], grad_norm=float(gn), samples_per_s=seen / el,
                       vram_gb=torch.cuda.max_memory_allocated() / 2 ** 30 if dev.type == "cuda" else 0.0)
            print(f"step {step}/{a.steps} " + " ".join(f"{k}={v:.4g}" for k, v in rec.items()), flush=True)
            log(step, rec); acc_m = {}; t0 = time.time(); seen = 0
        if step % a.eval_every == 0 or step == a.steps:
            ev = evaluate(ema or model, val_loader, a, dev, amp)
            if ev:
                print("eval", ev, flush=True); log(step, ev)
                if ev.get("val/loss", best) < best:
                    best = ev["val/loss"]; save(run / "best.pt", model=(ema or model).state_dict(), step=step, metrics=ev, args=vars(a))
        if step % a.save_every == 0 or step == a.steps:
            save(run / "last.pt", model=model.state_dict(), opt=opt.state_dict(), scaler=scaler.state_dict(),
                 ema=ema.state_dict() if ema is not None else None, step=step, args=vars(a),
                 rng={"py": random.getstate(), "np": np.random.get_state(), "torch": torch.get_rng_state()})
    print(f"done. best val/loss={best:.4g} -> {run}")


if __name__ == "__main__":
    main(get_args())
