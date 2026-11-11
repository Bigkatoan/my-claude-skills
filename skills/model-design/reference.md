# Building blocks: when to use what, and the pitfalls

Code for every block is in `blocks.py` (self-test: `python blocks.py`). Copy the blocks into `model.py` instead of importing them across projects.

| Block | Use when | Pitfalls |
|---|---|---|
| `ConvNeXtBlock` | Strong conv backbone for classification/encoders, small batches are fine (LayerNorm) | LayerScale 1e-6 makes it learn slowly at first; `drop_path` 0.1–0.2 only for large models/long training |
| `ResBlock` (GN-SiLU-Conv, AdaGN) | VAE encoder/decoder, diffusion U-Net | Last conv zero-initialised → identity block; with very few channels use GroupNorm `groups=min(32,C)` |
| `Attention` (SDPA, QK-norm, RoPE, cross) | Tokens/patches, text conditioning | Don't hand-write softmax; QK-norm keeps bf16 stable; masks use bool (True = attend) or additive float |
| `TransformerBlock` (pre-norm; adaLN-zero) | ViT/DiT; `cond_dim` for timestep/class conditioning | adaLN-zero → identity block at init; the last LayerNorm before the head is required |
| `PatchEmbed` + `sincos_2d` | ViT on images | Change resolution → interpolate/recompute the position embedding; patch 16 at 224 = 196 tokens |
| `rope_1d`/`apply_rope` | Sequences of variable length | Apply to q, k only (not v); head dim must be even |
| `timestep_embedding` | Diffusion / flow matching | Go through an MLP (Linear-SiLU-Linear) before using it as cond |
| `DiagonalGaussian` | VAE latent | Compute KL in fp32; clamp logvar; `free_bits` per channel against posterior collapse |
| `VectorQuantizer` | VQ-VAE / image tokenizer | Monitor codebook usage (perplexity, % codes used); dead codes → l2-normalised codes (already done) / reset |

## VAE / autoencoder for images (the current direction in `~/VAE`)
- Architecture: Conv stem → [ResBlock×2 + Downsample]×L → mid (ResBlock + Attention at the lowest resolution) → conv → `2·z` channels (μ, logσ²).
  The decoder mirrors it, using nearest-upsample + conv (avoids ConvTranspose checkerboarding).
- Downsampling factor f and latent channels z: f=8, z=4 (SD-VAE) ≈ compression 48×; f=16 needs z=16–32 to keep detail.
- Loss: L1/L2 recon + LPIPS (perceptual, weight ~0.1–1) + β·KL (β very small, 1e-6–1e-4 for a latent-diffusion VAE; β≈1 for a "true" generative VAE)
  + an optional patch GAN starting after N steps (adaptive weight per the last-layer gradient, as in taming/SD).
- Metrics: rFID, PSNR, SSIM, LPIPS on a fixed val set (e.g. 10k images of CC3M val/ImageNet val); also check the latent's statistics (mean/std per channel) if it will be used for diffusion.
- Posterior collapse: KL→0 and the latent carries no information → KL annealing, free bits, weaken the decoder, check the β scale against the recon scale (sum vs mean).

## Choosing a size for the RTX 3060 12GB (bf16, AdamW)
- ViT-S/16 (22M) at 224: bs ~128–192. ViT-B/16 (86M): bs ~48–64 (+ grad checkpointing for more).
- SD-VAE (~84M, f8) at 256: bs ~8–12 including LPIPS; to train from scratch, start at 128px or with a small model (~20–30M).
- Conv nets are memory-heavy because of activations at high resolution → use `channels_last` + bf16, downsample early with a stem.

## Porting an architecture from a paper
1. Find the official code / timm / diffusers first; if it exists, use it as the reference and compare outputs with the same weights (`torch.allclose`, atol 1e-4 in fp32).
2. Get the shape of every stage from the table in the paper and write it as comments; `model_report` must match the param count in the paper (±1%).
3. Note any detail the paper leaves out (init, norm eps, drop path, position embedding interpolation) and how you chose to handle it.
