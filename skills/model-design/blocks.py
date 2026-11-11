"""Tested building blocks (torch >= 2.1). Copy what you need into model.py.
Run `python blocks.py` to self-test (shapes + backward) on CPU/GPU."""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


# ----------------------------------------------------------------------------- conv
class ConvNeXtBlock(nn.Module):
    """x: (B,C,H,W) -> same. dw7x7 -> LN -> MLP(4x) -> LayerScale, residual."""
    def __init__(self, dim, ls_init=1e-6, drop_path=0.0):
        super().__init__()
        self.dw = nn.Conv2d(dim, dim, 7, padding=3, groups=dim)
        self.norm = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(nn.Linear(dim, 4 * dim), nn.GELU(), nn.Linear(4 * dim, dim))
        self.gamma = nn.Parameter(ls_init * torch.ones(dim))
        self.dp = drop_path

    def forward(self, x):
        y = self.dw(x).permute(0, 2, 3, 1)           # (B,H,W,C)
        y = (self.mlp(self.norm(y)) * self.gamma).permute(0, 3, 1, 2)
        if self.training and self.dp > 0:
            y = y * x.new_empty(x.shape[0], 1, 1, 1).bernoulli_(1 - self.dp) / (1 - self.dp)
        return x + y


class ResBlock(nn.Module):
    """GroupNorm-SiLU-Conv x2 (+ optional time/cond embedding via AdaGN scale-shift). Used in VAE/U-Net."""
    def __init__(self, cin, cout, emb_dim=0, groups=32):
        super().__init__()
        self.n1 = nn.GroupNorm(min(groups, cin), cin); self.c1 = nn.Conv2d(cin, cout, 3, padding=1)
        self.n2 = nn.GroupNorm(min(groups, cout), cout); self.c2 = nn.Conv2d(cout, cout, 3, padding=1)
        nn.init.zeros_(self.c2.weight); nn.init.zeros_(self.c2.bias)          # starts as identity
        self.emb = nn.Linear(emb_dim, 2 * cout) if emb_dim else None
        self.skip = nn.Conv2d(cin, cout, 1) if cin != cout else nn.Identity()

    def forward(self, x, emb=None):                 # x: (B,Cin,H,W), emb: (B,E)
        h = self.c1(F.silu(self.n1(x)))
        h = self.n2(h)
        if self.emb is not None:
            s, b = self.emb(F.silu(emb))[:, :, None, None].chunk(2, 1)
            h = h * (1 + s) + b
        return self.skip(x) + self.c2(F.silu(h))


# ----------------------------------------------------------------------------- transformer
class Attention(nn.Module):
    """x: (B,N,D) [, ctx: (B,M,D)] -> (B,N,D). Self- or cross-attention via SDPA (flash on GPU)."""
    def __init__(self, dim, heads=8, qk_norm=True):
        super().__init__()
        self.h = heads; self.q = nn.Linear(dim, dim); self.kv = nn.Linear(dim, 2 * dim); self.o = nn.Linear(dim, dim)
        self.qn = nn.LayerNorm(dim // heads) if qk_norm else nn.Identity()
        self.kn = nn.LayerNorm(dim // heads) if qk_norm else nn.Identity()

    def forward(self, x, ctx=None, rope=None, mask=None, causal=False):
        B, N, D = x.shape; ctx = x if ctx is None else ctx
        q = self.q(x).view(B, N, self.h, -1).transpose(1, 2)                         # (B,h,N,d)
        k, v = self.kv(ctx).view(B, ctx.shape[1], 2, self.h, -1).permute(2, 0, 3, 1, 4)
        q, k = self.qn(q), self.kn(k)
        if rope is not None:
            q, k = apply_rope(q, rope), apply_rope(k, rope)
        y = F.scaled_dot_product_attention(q, k, v, attn_mask=mask, is_causal=causal)
        return self.o(y.transpose(1, 2).reshape(B, N, D))


class TransformerBlock(nn.Module):
    """Pre-norm block; optional cross-attn; adaLN-zero conditioning (DiT) when cond_dim > 0."""
    def __init__(self, dim, heads=8, mlp_ratio=4.0, cross=False, cond_dim=0):
        super().__init__()
        self.n1 = nn.LayerNorm(dim, elementwise_affine=not cond_dim); self.attn = Attention(dim, heads)
        self.nx = nn.LayerNorm(dim) if cross else None; self.xattn = Attention(dim, heads) if cross else None
        self.n2 = nn.LayerNorm(dim, elementwise_affine=not cond_dim)
        self.mlp = nn.Sequential(nn.Linear(dim, int(dim * mlp_ratio)), nn.GELU(approximate="tanh"), nn.Linear(int(dim * mlp_ratio), dim))
        self.ada = nn.Sequential(nn.SiLU(), nn.Linear(cond_dim, 6 * dim)) if cond_dim else None
        if self.ada is not None:
            nn.init.zeros_(self.ada[1].weight); nn.init.zeros_(self.ada[1].bias)   # adaLN-zero: block = identity at init

    def forward(self, x, ctx=None, cond=None, rope=None):
        if self.ada is not None:
            s1, b1, g1, s2, b2, g2 = self.ada(cond)[:, None].chunk(6, -1)
            x = x + g1 * self.attn(self.n1(x) * (1 + s1) + b1, rope=rope)
            if self.xattn is not None:
                x = x + self.xattn(self.nx(x), ctx)
            return x + g2 * self.mlp(self.n2(x) * (1 + s2) + b2)
        x = x + self.attn(self.n1(x), rope=rope)
        if self.xattn is not None:
            x = x + self.xattn(self.nx(x), ctx)
        return x + self.mlp(self.n2(x))


class PatchEmbed(nn.Module):
    """(B,C,H,W) -> (B, H/p*W/p, D)."""
    def __init__(self, cin, dim, p):
        super().__init__(); self.proj = nn.Conv2d(cin, dim, p, p)

    def forward(self, x):
        return self.proj(x).flatten(2).transpose(1, 2)


def sincos_2d(h, w, dim, device=None):
    """Fixed 2D sin-cos position embedding (h*w, dim)."""
    y, x = torch.meshgrid(torch.arange(h, device=device), torch.arange(w, device=device), indexing="ij")
    om = 1.0 / 10000 ** (torch.arange(dim // 4, device=device) / (dim // 4))
    out = [f(c.flatten()[:, None].float() * om[None]) for c in (y, x) for f in (torch.sin, torch.cos)]
    return torch.cat(out, 1)


def rope_1d(n, d, base=10000.0, device=None):
    """RoPE cos/sin tables for head dim d: returns (cos, sin) each (n, d)."""
    inv = 1.0 / base ** (torch.arange(0, d, 2, device=device).float() / d)
    f = torch.outer(torch.arange(n, device=device).float(), inv)
    f = torch.cat([f, f], -1)
    return f.cos(), f.sin()


def apply_rope(x, rope):                             # x: (B,h,N,d)
    cos, sin = rope
    x1, x2 = x.chunk(2, -1)
    return x * cos + torch.cat([-x2, x1], -1) * sin


def timestep_embedding(t, dim, max_period=10000):
    """t: (B,) float -> (B, dim) sinusoidal (diffusion / flow matching)."""
    half = dim // 2
    f = torch.exp(-math.log(max_period) * torch.arange(half, device=t.device) / half)
    a = t.float()[:, None] * f[None]
    return torch.cat([a.cos(), a.sin()], -1)


# ----------------------------------------------------------------------------- latent models
class DiagonalGaussian:
    """VAE posterior from (B, 2z, ...) moments. kl() per sample, summed over latent dims (fp32)."""
    def __init__(self, moments):
        self.mu, logvar = moments.float().chunk(2, 1)
        self.logvar = logvar.clamp(-30, 20); self.std = (0.5 * self.logvar).exp()

    def sample(self):
        return self.mu + self.std * torch.randn_like(self.std)

    def kl(self, free_bits=0.0):
        kl = 0.5 * (self.mu ** 2 + self.logvar.exp() - 1 - self.logvar)      # per element
        if free_bits > 0:                                                     # per-channel floor vs posterior collapse
            kl = kl.mean(dim=tuple(range(2, kl.ndim)), keepdim=True).clamp(min=free_bits).expand_as(kl)
        return kl.flatten(1).sum(1)


class VectorQuantizer(nn.Module):
    """VQ with straight-through, l2-normalised codes (stable usage). z: (B,C,H,W) -> zq, loss, idx."""
    def __init__(self, n_codes, dim, beta=0.25):
        super().__init__(); self.cb = nn.Embedding(n_codes, dim); self.beta = beta
        nn.init.uniform_(self.cb.weight, -1 / n_codes, 1 / n_codes)

    def forward(self, z):
        B, C, H, W = z.shape
        zf = F.normalize(z.permute(0, 2, 3, 1).reshape(-1, C).float(), dim=1)
        cb = F.normalize(self.cb.weight.float(), dim=1)
        idx = (zf @ cb.t()).argmax(1)
        zq = cb[idx]
        loss = F.mse_loss(zq, zf.detach()) + self.beta * F.mse_loss(zf, zq.detach())
        zq = (zf + (zq - zf).detach()).view(B, H, W, C).permute(0, 3, 1, 2).to(z.dtype)
        return zq, loss, idx.view(B, H, W)


# ----------------------------------------------------------------------------- self-test
if __name__ == "__main__":
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(0)

    def chk(name, m, *inp, **kw):
        m = m.to(dev); out = m(*[i.to(dev) for i in inp], **kw)
        o = out[0] if isinstance(out, tuple) else out
        extra = sum(t for t in out[1:] if torch.is_tensor(t) and t.ndim == 0) if isinstance(out, tuple) else 0
        ((o.float() * torch.randn_like(o.float())).mean() + extra).backward()
        miss = [n for n, p in m.named_parameters() if p.grad is None]
        print(f"ok {name:22} {tuple(inp[0].shape)} -> {tuple(o.shape)}  no-grad params: {miss}")

    chk("ConvNeXtBlock", ConvNeXtBlock(64), torch.randn(2, 64, 16, 16))
    chk("ResBlock+emb", ResBlock(64, 128, emb_dim=32), torch.randn(2, 64, 16, 16), emb=torch.randn(2, 32).to(dev))
    rope = tuple(t.to(dev) for t in rope_1d(10, 32))
    chk("Attention+RoPE", Attention(256, 8), torch.randn(2, 10, 256), rope=rope)
    chk("TransformerBlock", TransformerBlock(256, 8, cross=True), torch.randn(2, 10, 256), ctx=torch.randn(2, 7, 256).to(dev))
    chk("DiT block (adaLN0)", TransformerBlock(256, 8, cond_dim=64), torch.randn(2, 10, 256), cond=torch.randn(2, 64).to(dev))
    chk("PatchEmbed", PatchEmbed(3, 192, 16), torch.randn(2, 3, 224, 224))
    print("ok sincos_2d", tuple(sincos_2d(14, 14, 192).shape), "| timestep_emb", tuple(timestep_embedding(torch.rand(4), 128).shape))
    post = DiagonalGaussian(torch.randn(2, 8, 32, 32)); print("ok DiagonalGaussian z", tuple(post.sample().shape), "kl", post.kl().shape, post.kl(0.1).shape)
    chk("VectorQuantizer", VectorQuantizer(512, 16), torch.randn(2, 16, 8, 8, requires_grad=True))
