---
name: manim-visualize
description: Use whenever the user asks to "visualize", "minh hoạ", "trực quan hoá", animate, or show how something works (architecture, algorithm, math, data flow). Default output is a Manim animation (mp4), picture-first with almost no text. Use plain matplotlib/static figures only if the user explicitly asks for a static image or chart.
---

# Visualize = Manim, picture-first

When the user says "visualize" (any language), make a **Manim** video unless they name another format.

## Hard rules (user preference, stated explicitly)
1. **Minimise text.** No sentences, no bullet lists, no paragraphs on screen. Express ideas with shapes, colour, motion, arrows, counts of objects, bar heights, icons.
2. **Formulas become pictures.** Never put a LaTeX/ASCII formula on screen. Draw it as a data-flow diagram: boxes with small glyphs (grid = conv/stencil, bars = norm/vector, curve = activation, matrix = linear), circles for + / x, arrows for flow, a moving dot for a token travelling through, a curved/polyline arrow for skip connections.
3. Allowed text: a title-free scene is fine; otherwise only 1-2 word tags under icons (<= 18pt, grey), numbers on bars/axes, and a single small footnote for the data setting. Add real text/captions/formulas **only if the user asks** ("thêm chữ", "kèm công thức", ...).
4. Use **real data** when it exists (real image colours, real masks/weights from the code or checkpoint), not made-up pictures. Say in the footnote when something is illustrative.
5. Honest content: if experiments contradict the story, the picture must show that (e.g. a bar chart including the better baseline). Mark seed counts.

## Environment on this machine
- Manim Community 0.19.1 installed with `pip install --user manim`; `ffmpeg` and `latex` exist. Avoid LaTeX anyway (use `Text`, font "DejaVu Sans").
- **Keep numpy at 1.26.4.** Installing/upgrading manim pulls numpy 2.x, which breaks `wandb` and therefore torch/timm imports. If numpy changes: `pip install --user "numpy==1.26.4"` and re-check `python3 -c "import torch,timm,torchvision,manim"`. Do this before touching anything that may share the env (training runs launched later will fail).
- GPU may be busy with training: Manim is CPU-only, so it is safe to render alongside.

## Workflow
1. Decide the 4-6 scenes, each with one idea and a picture of it. Pull real data first (numpy arrays from the model/checkpoint/cache).
2. Write `<name>_manim.py` next to the work (not in /tmp). One `Scene` class.
3. Render: `manim -qm --media_dir manim_media file.py SceneName` (720p30; use `-ql` for drafts, `-qh` only when asked). Output: `manim_media/videos/<file>/720p30/<Scene>.mp4`.
4. **Check frames before sending**: `ffprobe` the duration, grab ~8 frames with `ffmpeg -ss T -frames:v 1`, tile them and Read the sheet. Look for overlap, off-screen objects, leftovers. Fix and re-render.
5. Deliver with `SendUserFile` (status normal, display render) and a short summary in the user's language (Vietnamese for this user). Say which numbers/data the animation uses.

## Pitfalls already hit (Manim 0.19)
- `Rectangle(w, h)`: first positional arg is `color`. Always `Rectangle(width=..., height=...)`. `Square(side)` is fine.
- `mobject.align_to(np_array, dir)` fails on a plain vector; shift manually: `m.shift(RIGHT*(x - m.get_left()[0]))`.
- Colours from numpy: use `ManimColor.from_rgb([float(v)/255 for v in rgb])`; `rgb_to_color(ndarray)` raises TypeError.
- `Transform(x.copy(), y)` leaves the copy on screen; `self.add(copy)` first and `FadeOut(copy)` afterwards.
- Leave >= 0.5 unit between stacked groups (a bar chart under an equation overlapped once); frame is 14.2 x 8 units, safe area about x in [-6.5, 6.5], y in [-3.6, 3.6].
- Many `Square` cells (16x16 grids x several) render fine; use `LaggedStart`/`FadeIn(lag_ratio=...)` instead of per-cell loops of `self.play`.
- `FadeOut(*[m for m in self.mobjects])` at scene ends keeps the stage clean.

## Reusable pieces
`reference.py` in this folder has tested helpers: `cell_grid` (coloured n x n grid), `role`-style colour palettes, icon builders (norm bars, 3x3 stencil, ring-pattern grid, SiLU curve, matrix), `circ` for +/x, wire arrows, and a token dot flowing along a pipeline. Copy what you need into the scene file.
