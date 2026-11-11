---
name: pytorch-training
description: Use whenever the task is to train, fine-tune, resume, debug or speed up a PyTorch model - writing a train.py/training loop, choosing lr/batch/schedule, mixed precision, OOM, NaN/divergence, slow dataloader, checkpoints, running and monitoring long training jobs, comparing runs ("train", "huấn luyện", "fine-tune", "loss không giảm", "bị NaN", "OOM", "resume"). Pairs with `model-design` (architecture) and `datasets` (data location).
---

# Training models with PyTorch

This user's style: **plain PyTorch, a single `train.py` file, `argparse`, bf16 autocast, step-based training** (not epochs), no Lightning/Hydra.
Machine: **RTX 3060 12GB**, 12 CPU cores, 31GB RAM, torch 2.6 + cu124, timm, webdataset, accelerate, wandb, tensorboard.

## 1. Start from the template
`templates/train.py` (in this skill's folder) has been tested: bf16/fp16/fp32, grad accumulation, clipping, AdamW with no-decay groups,
warmup + cosine, EMA, `torch.compile`, channels_last, atomic checkpoints + full resume (opt, scaler, RNG), eval + `best.pt`,
`log.jsonl` (+ `--tb`, `--wandb`), samples/s, peak VRAM, and it saves the batch and stops when the loss goes NaN.
```bash
cp ~/.claude/skills/pytorch-training/templates/train.py <project>/train.py
python train.py --demo --steps 200          # check the machinery runs before plugging in the real model
```
Only fill in **3 hooks**: `build_model(a)`, `build_data(a)`, `compute_loss(model, batch, a) -> (loss, metrics)`.
Add your own flags in `get_args`. Keep the run-folder layout `runs/<name>/{args.json, log.jsonl, last.pt, best.pt}`.

## 2. Mandatory sanity ladder (before any long run)
Do them in order; if a step fails, fix it before moving on:
1. **Model report**: `model_report.py` (skill `model-design`) — params, FLOPs, VRAM, unused params, NaN.
2. **Loss at init** matches theory: classification ≈ `ln(C)`; MSE on normalised data ≈ variance (~1); VAE: KL ≈ 0, recon ≈ data variance.
   Way off → wrong init / loss scale / label.
3. **Overfit 1 batch**: `--overfit 1 --steps 300 --wd 0` → the loss must fall sharply toward ~0 (train acc → 100%).
   If it doesn't → bug in model/loss/labels/optimizer, *not* a hyperparameter problem.
4. **Check the data visually**: save a grid of a batch *after* augmentation and normalisation (denormalise it back) and look at it.
   Check the labels/captions match the images.
5. **Short run** of ~1–2k steps: loss falls steadily, grad_norm is stable, samples/s is stable, VRAM < 11GB.
6. Only then start the long run.

## 3. Default hyperparameters (adjust to the problem)
| | from scratch | fine-tune pretrained |
|---|---|---|
| optimizer | AdamW betas (0.9, 0.95), wd 0.05 | AdamW wd 0.01–0.05 |
| lr (bs≈256) | 1e-3 conv / 3e-4–1e-3 ViT | 1e-5–1e-4; head 10x the backbone |
| schedule | warmup 2–5% + cosine down to 10% | warmup short, cosine |
| clip | 1.0 | 1.0 |
| EMA | 0.999–0.9999 for generative/VAE/diffusion | optional |
- Changing batch size: scale lr linearly (SGD) or by √ (Adam) relative to the base bs, and keep warmup.
- Generative models (VAE/diffusion): report the EMA weights; lr 1e-4–2e-4 is the common starting point.

## 4. Fitting into 12GB (in order of what to try)
bf16 autocast (default) → reduce `--bs` + raise `--accum` to keep the effective bs →
`torch.utils.checkpoint` on heavy blocks → `F.scaled_dot_product_attention` (flash/mem-efficient) instead of hand-written attention →
`--channels_last` (conv) → 8-bit optimizer (bitsandbytes) if params are large → reduce resolution / token count.
Use `model_report.py` to estimate the maximum batch before running.

## 5. Throughput
- GPU util < 90% (`nvidia-smi dmon`) → bottleneck is the dataloader: `num_workers` 8–10, `pin_memory`, `persistent_workers=True`,
  `prefetch_factor` 4, decode/resize in the worker; with webdataset use `.shuffle(1000)`, `.batched()` in the worker, `WebLoader`.
- `--compile` usually gives +10–40% once shapes are fixed (drop_last=True). The first step is slow (compiling), that's normal.
- `cudnn.benchmark=True` and TF32 are already on in the template.

## 6. Diagnosing failures
| symptom | check |
|---|---|
| loss NaN/Inf | the template saves `nan_batch.pt` → check that batch; lower lr, check warmup, log/exp/div by 0, fp16 → switch to bf16, run softmax/loss in fp32 (`.float()`) |
| loss doesn't fall | overfit 1 batch; lr too low/high (try ×10, ÷10); is `model.train()` set; is `zero_grad` called; are any params left frozen |
| loss oscillates/spikes | lr too high, warmup too short, missing clip, batch too small, bad samples in the data |
| val worse than train early | data leakage/augmentation mismatch; BN in train mode during eval; normalisation differs between train and val |
| VAE posterior collapse (KL→0) | KL warmup/annealing, free bits, decoder too strong; watch KL per dimension |
| slow | profile: `torch.profiler` for ~20 steps, look at the dataloader time vs fwd/bwd |

## 7. Running long jobs (in this environment)
- Run in the background and write a log: `python train.py --name X ... > runs/X/stdout.log 2>&1` with `run_in_background`.
- Monitor with **Monitor**: tail the log, filtering for `step |eval|Traceback|Error|nan|Killed|CUDA out of memory`,
  and include a "no new log for N minutes" check (to catch hangs). Silence ≠ success.
- If the job dies: `--resume` continues from `last.pt` (state is saved every `--save_every`).
- Data: always take it from `~/datasets` (skill `datasets`); never copy data into the project.

## 8. Reporting results honestly
- Each config needs ≥ 2–3 seeds before claiming a difference smaller than ~1%; report mean ± std and the number of seeds.
- Compare against a strong baseline at **the same** compute budget (steps × bs) and the same data/augmentation.
- Report: params, FLOPs, steps, effective bs, lr, best and last metric, EMA or not, training time on the 3060.
- If a result contradicts the hypothesis, say so plainly.
