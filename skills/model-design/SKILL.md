---
name: model-design
description: Use whenever the task is to design, modify, review or compare a neural-network architecture in PyTorch - new model, new block/layer, VAE/autoencoder/tokenizer, encoder/decoder, attention/conv variants, choosing model size, porting a paper's architecture, ablations ("thiết kế model", "kiến trúc", "viết model", "thêm block", "model này bao nhiêu params/FLOPs"). Pairs with `pytorch-training` (training it) and `datasets`.
---

# Designing AI models (PyTorch)

Goal: a model that is **correct, measured and comparable** before you spend GPU time training it. Machine: RTX 3060 12GB.

## Workflow
1. **Pin down the spec** (write it as a short comment at the top of `model.py`):
   input (shape, dtype, range), output, loss, target metric, compute budget (params, FLOPs/sample,
   VRAM for bs=X on 12GB, wall time on the 3060), and the hard constraints (resolution, latency, pretrained weights).
2. **Baseline first.** Take a known architecture (timm, diffusers, torchvision, or the paper's reference code) at a matching size,
   measure it with `model_report.py`, and train it with the same recipe. Every new idea must beat this baseline at the **same compute budget**.
3. **Write the model** following the conventions below. Change one thing at a time against the baseline.
4. **Measure** with `tools/model_report.py` (params per module, output shape, FLOPs, VRAM fwd+bwd, throughput,
   unused params / grad = 0 / NaN):
   ```bash
   python ~/.claude/skills/model-design/tools/model_report.py model.py:build_model --kwargs '{"dim":256}' --input 16,3,224,224 --bf16
   python ~/.claude/skills/model-design/tools/model_report.py timm:vit_small_patch16_224 --input 64,3,224,224 --bf16   # baseline
   ```
5. **Write tests** (`test_model.py`, run with pytest, < 30s on CPU or GPU): output shape for several batch sizes/resolutions;
   gradient reaches every param; a deterministic seed gives the same output; the model is invariant/equivariant as designed (if applicable);
   bf16 and fp32 outputs are close; `torch.compile(model)` runs.
6. Hand it to the `pytorch-training` skill: sanity ladder (init loss, overfit 1 batch) → short run → long run.
7. **Ablation table**: each component on/off, same seeds/steps, with params & FLOPs columns. Keep only components that actually help.

## Code conventions
- One `model.py` file: a `Config` dataclass + `build_model(**kwargs)`; no global state; no hard-coded device.
- Every `forward` has a comment with the shape: `# x: (B, C, H, W) -> (B, N, D)`. Use `einops.rearrange` instead of chained view/permute.
- Attention: `F.scaled_dot_product_attention` (flash / mem-efficient on the 3060), don't write softmax(QK^T) by hand.
- Normalisation: pre-norm (`x + f(norm(x))`) for transformers; GroupNorm/LayerNorm for small batches (BatchNorm is unstable when bs < 16).
- Init: trunc_normal(0.02) for Linear/Embedding in transformers; **zero-init the last layer of each residual branch**
  (or LayerScale/gamma = 0 / small) so the model starts close to identity → stable deep training.
  Note: zero-init makes `model_report` show grad = 0 at step 0 for the earlier layers in that branch — that's intended.
- Run softmax / loss / logsumexp / KL in fp32 (`.float()`) even when the model runs under bf16.
- Avoid `.item()`/Python branches that depend on tensor values inside `forward` (they break `torch.compile` and slow things down).
- `nn.ModuleList`/`ModuleDict` for submodules; buffers (`register_buffer(persistent=False)`) for constants such as RoPE tables and masks.

## Sizing rules (fast estimates)
- Linear d→d: d² params, 2·d² FLOPs per token. Transformer block (MLP ratio 4): ~12·d² params, ~24·d²·N + 4·N²·d FLOPs for N tokens.
- Conv k×k Cin→Cout on H×W output: k²·Cin·Cout params, 2·k²·Cin·Cout·H·W FLOPs.
- Training ≈ 3× forward FLOPs. VRAM ≈ weights + grads + AdamW (16 bytes/param fp32 in total) + activations (∝ bs × resolution).
- 3060: plan on ~25–35 TFLOPS of effective bf16 (≈40–50% of peak) to estimate training time: time ≈ 3·FLOPs/sample·samples / 30e12.

## Common building blocks
See `reference.md` (same folder): ConvNeXt/ResNet blocks, ViT patchify + RoPE/2D sincos, cross-attention,
VAE (encoder → μ, logσ² → reparameterise → decoder; KL; β; free bits), VQ tokenizer (codebook, commitment loss, EMA codebook),
U-Net for diffusion (time embedding, AdaGN), and the pitfalls of each block.

## Reviewing an architecture (checklist)
- [ ] Does the spec match the code (shape, range, loss)? Do the parameters actually used match the parameters declared (no unused params)?
- [ ] Does the receptive field / token count cover the information the task needs?
- [ ] Is there an information bottleneck in the wrong place (downsampling too early, latent too small)?
- [ ] Is the normalisation compatible with the batch size? Is there a residual/skip path for gradients?
- [ ] Params/FLOPs comparable with the baseline? Were the gains in the claim measured at the same budget?
