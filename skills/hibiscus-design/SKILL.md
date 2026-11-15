---
name: hibiscus-design
description: Use whenever a project is part of the Hibiscus family or should use the Hibiscus look - letrain / Hibiscus training platform, Robot Ops, any app or page the user calls "Hibiscus", "giao diện Hibiscus", "pixel garden", "linh vật Hibi", or asks to reuse "asset Hibiscus" / "bộ asset hibiscus". Also use when adding pixel sprites, mascot animations, icons, theme colours or dark mode to those projects. Always take assets from ~/hibiscus-assets (github Bigkatoan/hibiscus-assets) instead of copying files from another project or drawing new ones ad hoc.
---

# Hibiscus design system — always use `~/hibiscus-assets`

Single source of truth: `~/hibiscus-assets` (private repo `Bigkatoan/hibiscus-assets`). It holds the
sprite sources (`design/`), built files (`dist/pixel/`), CSS (`css/`), React components (`react/`),
fonts, brand files and the style guide (`docs/style-guide.md` — read it before designing).

If the folder is missing: `gh repo clone Bigkatoan/hibiscus-assets ~/hibiscus-assets`.
Before syncing, `git -C ~/hibiscus-assets pull --ff-only` (ignore failure when offline).

## Put the assets into a project
```bash
~/hibiscus-assets/tools/sync.sh <frontend-dir>              # -> public/pixel, public/fonts, src/hibiscus/
~/hibiscus-assets/tools/sync.sh <frontend-dir> --favicon     # also copy the hibiscus favicon
# non-Vite layouts: --public <static dir> --src <code dir>
```
Never hand-edit the synced copies (`public/pixel`, `src/hibiscus`) — change the repo, rebuild, re-sync.
Mention the synced version (`src/hibiscus/VERSION`) in your summary.

## Use them
```tsx
import './hibiscus/hibiscus.css'          // or only motion.css when the app already has its own skin
import { Hibi, PixelAnim, PxIcon, Sprite, Garden, Petals } from './hibiscus/PixelAnim'

<Hibi mood="idle|wave|happy|working|sleep|sad" size="hero|mini" />  // robot arm holding a hibiscus
<a className="px-hover"><PixelAnim name="icon_train" /> Tasks</a>  // colour icon, animates on hover
<button><PxIcon name="plus" /> Add</button>   // 8x8 UI glyph, currentColor
<Garden />          // grass + swaying tufts + Hibi + butterfly (sidebar bottom)
<Petals count={10} />  // falling petals (login / celebration), parent must be position: relative
```
Plain HTML: see the comment at the top of `css/motion.css`.

Mood mapping: empty state → `idle`; login/onboarding → `wave`; loading/running → `working`;
success → `happy`; queued/paused → `sleep`; error/failed → `sad`. One looping mascot per screen
(plus the garden). Icon metaphors are in the style guide (seed bag = dataset/stock, crate = upload/
orders, sprouting pot = tasks/training, basket = model, chip = GPU/components, scroll = docs/logs,
clock = calendar/queue, gear = settings, robot arm = products/robots).

## Rules the user has set (do not regress)
- **One pixel unit:** 1 art pixel = 2 CSS px for every sprite, glyph, frame (8 px 9-slice border),
  rim, shadow and movement step. No `scale` props / per-use zoom. Need another size → draw it at
  another resolution (glyph 8×8, icon 16×16, Hibi mini 24×24, Hibi hero 48×48) in `design/`.
- **Every icon is Hibiscus:** colour 16×16 sprites for navigation/feature icons, `PxIcon` glyphs for
  buttons/inputs/inline. Never use lucide/heroicons/emoji icons in Hibiscus apps; if a glyph or icon
  is missing, add it to `design/glyphs.py` / `design/icons_extra.py`, rebuild, re-sync.
- **Readable text:** Nunito for all UI text, headings included. **No pixel fonts** (Tiny5/VT323) unless
  the user explicitly asks; they were rejected as hard to read.
- **Dark mode:** flat indigo frames + hard shadow; never wood frames (`ui_panel_night`) on cards.
  Sprites get the 1 px moonlight rim from `motion.css` automatically.
- **Mascot:** Hibi is the robot arm holding a hibiscus. The old TV-head robot was retired because it
  looked too familiar — never bring it back or draw a similar boxy-screen robot.
- **Originality / legal:** all art is drawn from code in `design/`. Never copy, trace or imitate
  sprites, characters, fonts or UI of existing games, and never describe a product as looking like a
  specific game.
- Pixel art: integer scales only, `image-rendering: pixelated`, `steps()` animation, square corners,
  hard offset shadows, respect `prefers-reduced-motion` (handled by `motion.css`).

## Adding or changing art
1. Edit `design/sprites.py` (static grids), `design/mascot.py` (arm poses, joint angles) or
   `design/anims.py` (frame lists), using only the palette in `sprites.py`.
2. `python3 ~/hibiscus-assets/design/build.py` (needs Pillow) → look at
   `docs/preview/_sheet.png` (Read it) and fix anything off-canvas or unreadable.
3. Update `docs/style-guide.md` if a new sprite/animation/rule is added; commit `design/ dist/
   docs/ react/` together and push; then re-sync the projects that use it.
4. For UI checks, screenshot both colour schemes (Playwright image `hibiscus-playwright:1.49.1`).
