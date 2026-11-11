"""Tested reference scene (radial token-mixer explainer, picture-only). Copy helpers/idioms from here.
IMG path and role() are specific to that example; replace them. Bar-chart numbers are illustrative."""
"""Manim (picture-only version): how OmniRadial works. Formulas are drawn as data-flow diagrams.
Render:  manim -qm manim_omniradial_visual.py OmniRadialVisual"""
import numpy as np
from manim import *
from PIL import Image

IMG = "../../assets/samples/sample_505_bird.jpg"
BG = "#0f1115"
COL = {"self": YELLOW, "n1": "#ff8a3d", "N": "#4cc9f0", "S": "#f72585", "W": "#80ed99", "E": "#b388ff", "far": "#6b7280"}


def role(qr, qc, r, c):
    dr, dc = r - qr, c - qc
    d = max(abs(dr), abs(dc))
    if d == 0: return "self"
    if d == 1: return "n1"
    if d <= 4:
        if dr < 0: return "N"
        if dr > 0: return "S"
        return "W" if dc < 0 else "E"
    return "far"


def cell_grid(g, size, center=ORIGIN, colors=None, fill=GREY_E, op=0.95, stroke=0.5):
    cell = size / g; out = VGroup()
    for r in range(g):
        for c in range(g):
            col = fill if colors is None else colors[r][c]
            sq = Square(cell * 0.95, stroke_width=stroke, stroke_color=GREY_B, fill_color=col, fill_opacity=op)
            sq.move_to(center + np.array([(c - (g - 1) / 2) * cell, ((g - 1) / 2 - r) * cell, 0])); out.add(sq)
    return out


def tag(s, fs=18, col=GREY_B):
    return Text(s, font="DejaVu Sans", font_size=fs, color=col)


class OmniRadialVisual(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ---------------------------------------------------------------- 1 patchify (colours = real patch means)
        pil = Image.open(IMG).convert("RGB").resize((128, 128))
        a = np.asarray(pil, dtype=float).reshape(16, 8, 16, 8, 3).mean((1, 3))
        tok_cols = [[ManimColor.from_rgb([float(v) / 255 for v in a[r, c]]) for c in range(16)] for r in range(16)]
        img = ImageMobject(IMG).set_height(4.4).shift(LEFT * 3.6)
        self.play(FadeIn(img))
        L, T_, S = img.get_left()[0], img.get_top()[1], img.height
        lines = VGroup(*[Line([L + S * i / 16, T_, 0], [L + S * i / 16, T_ - S, 0], stroke_width=.8, color=WHITE, stroke_opacity=.7) for i in range(17)],
                       *[Line([L, T_ - S * i / 16, 0], [L + S, T_ - S * i / 16, 0], stroke_width=.8, color=WHITE, stroke_opacity=.7) for i in range(17)])
        self.play(Create(lines), run_time=1.2)
        tokens = cell_grid(16, 4.4, center=RIGHT * 3.4, colors=tok_cols, op=1)
        pic = [(3, 9), (7, 4), (11, 12)]
        for (r, c) in pic:
            box = Square(S / 16, stroke_color=YELLOW, stroke_width=3, fill_opacity=0).move_to([L + S * (c + .5) / 16, T_ - S * (r + .5) / 16, 0])
            tgt = tokens[r * 16 + c]
            self.play(Create(box), run_time=.35)
            self.play(box.animate.become(tgt.copy().set_stroke(YELLOW, 3)), run_time=.7)
        self.play(FadeIn(tokens, lag_ratio=0.003, run_time=1.6))
        self.wait(.6)
        self.play(FadeOut(img), FadeOut(lines), FadeOut(tokens), *[FadeOut(m) for m in self.mobjects if isinstance(m, Square)])

        # ---------------------------------------------------------------- 2 what one token reads
        G = 16; size = 5.2; ctr = LEFT * 3.4
        grid = cell_grid(G, size, center=ctr, op=0.95); cw = size / G
        q = lambda r, c: grid[r * G + c]
        pos = lambda r, c: q(r, c).get_center()
        qr = qc = 7
        self.play(FadeIn(grid, run_time=.8))
        self.play(q(qr, qc).animate.set_fill(COL["self"], 1).scale(1.3))
        # weight bars panel on the right
        base_y = -2.2; bx0 = 1.6
        bars = VGroup(); heights = [.9, 1.5, .6, 1.8, 1.1, .5, 1.4, .8]       # 8 individual weights (illustrative)
        # r = 1 : 8 neighbours, 8 arrows, 8 bars
        nb = [(qr + dr, qc + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
        for i, (r, c) in enumerate(nb):
            self.play(q(r, c).animate.set_fill(COL["n1"], 1), run_time=.12)
        arrs = VGroup(*[Arrow(pos(r, c), pos(qr, qc), buff=cw * .45, color=COL["n1"], stroke_width=3, max_tip_length_to_length_ratio=.5) for (r, c) in nb])
        bar_n = VGroup(*[Rectangle(width=.28, height=h, fill_color=COL["n1"], fill_opacity=1, stroke_width=0).move_to([bx0 + i * .36, base_y + h / 2, 0]) for i, h in enumerate(heights)])
        self.play(LaggedStart(*[GrowArrow(x) for x in arrs], lag_ratio=.08), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bar_n], lag_ratio=.08), run_time=1.6)
        # sectors
        sec = {k: [(r, c) for r in range(G) for c in range(G) if role(qr, qc, r, c) == k] for k in "NSWE"}
        bar_s = VGroup(); arr_s = VGroup()
        for j, (k, h) in enumerate(zip("NSWE", (1.6, 1.0, 1.9, 1.2))):
            self.play(*[q(r, c).animate.set_fill(COL[k], 1) for (r, c) in sec[k]], run_time=.5)
            cen = np.mean([pos(r, c) for (r, c) in sec[k]], axis=0)
            ar = Arrow(cen, pos(qr, qc), buff=cw * .6, color=COL[k], stroke_width=7); arr_s.add(ar)
            b = Rectangle(width=.5, height=h, fill_color=COL[k], fill_opacity=1, stroke_width=0).move_to([bx0 + 8 * .36 + .3 + j * .6, base_y + h / 2, 0]); bar_s.add(b)
            self.play(GrowArrow(ar), GrowFromEdge(b, DOWN), run_time=.55)
        # far field: all grey, ONE arrow / ONE bar
        far = [(r, c) for r in range(G) for c in range(G) if role(qr, qc, r, c) == "far"]
        self.play(*[q(r, c).animate.set_fill(COL["far"], 1) for (r, c) in far], run_time=.8)
        for _ in range(2):
            self.play(*[q(r, c).animate.set_fill("#9ca3af", 1) for (r, c) in far], run_time=.3)
            self.play(*[q(r, c).animate.set_fill(COL["far"], 1) for (r, c) in far], run_time=.3)
        far_ar = Arrow(pos(0, 0), pos(qr, qc), buff=cw * .6, color="#9ca3af", stroke_width=10)
        far_bar = Rectangle(width=.9, height=1.0, fill_color=COL["far"], fill_opacity=1, stroke_width=0).move_to([bx0 + 8 * .36 + .3 + 4 * .6 + .5, base_y + .5, 0])
        self.play(GrowArrow(far_ar), GrowFromEdge(far_bar, DOWN))
        axis = Line([bx0 - .3, base_y, 0], [bx0 + 7.0, base_y, 0], color=GREY_B, stroke_width=2)
        self.add(axis); self.wait(1.6)
        # query moves
        keep = VGroup(arrs, arr_s, far_ar, bar_n, bar_s, far_bar, axis)
        self.play(FadeOut(keep))
        for (nr, nc) in [(3, 3), (1, 12), (14, 2), (12, 12), (7, 7)]:
            self.play(*[q(r, c).animate.set_fill(COL[role(nr, nc, r, c)], 1) for r in range(G) for c in range(G)], run_time=.8)
        # translation / border cue: pattern follows
        self.wait(.4)
        self.play(FadeOut(grid))

        # ---------------------------------------------------------------- 3 gated block as a data-flow diagram
        def box(w, h, col=GREY_D): return RoundedRectangle(corner_radius=.1, width=w, height=h, stroke_color=GREY_B, fill_color=col, fill_opacity=1, stroke_width=1.5)
        def glyph_ln():
            bs = VGroup(*[Rectangle(width=.1, height=hh, fill_color=BLUE_C, fill_opacity=1, stroke_width=0) for hh in (.15, .4, .25, .5, .3)]).arrange(RIGHT, buff=.05, aligned_edge=DOWN)
            return VGroup(box(.9, .8), bs.scale(.9)).copy()
        def glyph_local():
            g3 = cell_grid(3, .6, colors=[[COL["n1"]] * 3, [COL["n1"], COL["self"], COL["n1"]], [COL["n1"]] * 3]); return VGroup(box(.9, .8), g3)
        def glyph_global():
            cols = [[COL[role(3, 3, r, c)] for c in range(7)] for r in range(7)]; return VGroup(box(.9, .8), cell_grid(7, .62, colors=cols, stroke=.2))
        def glyph_silu():
            ax = Axes(x_range=[-3, 3], y_range=[-.5, 3], x_length=.7, y_length=.6, tips=False, axis_config={"stroke_width": 1})
            return VGroup(box(.9, .8), ax, ax.plot(lambda x: x / (1 + np.exp(-x)), color=YELLOW, stroke_width=3))
        def glyph_lin():
            M = cell_grid(4, .55, colors=[[("#4cc9f0" if (r + c) % 2 else "#2b6cb0") for c in range(4)] for r in range(4)], stroke=.2); return VGroup(box(.9, .8), M)
        def circ(sym, col=WHITE): return VGroup(Circle(.26, stroke_color=col, stroke_width=2, fill_color=BG, fill_opacity=1), Text(sym, font_size=26, color=col, font="DejaVu Sans"))
        P = {"x": LEFT * 6.2, "ln": LEFT * 4.6, "loc": [-2.6, 1.5, 0], "glo": [-2.6, .2, 0], "sum": [-.7, .85, 0], "sil": [-2.6, -1.6, 0], "mul": [.9, 0, 0], "lin": [2.3, 0, 0], "gam": [3.6, 0, 0], "add": [4.8, 0, 0]}
        xt = VGroup(*[Square(.13, fill_color=c, fill_opacity=1, stroke_width=0) for c in (RED_C, ORANGE, YELLOW, GREEN_C, BLUE_C, PURPLE_C)]).arrange(DOWN, buff=0).move_to(P["x"])
        ln = glyph_ln().move_to(P["ln"]); loc = glyph_local().move_to(P["loc"]); glo = glyph_global().move_to(P["glo"]); sil = glyph_silu().move_to(P["sil"])
        sm = circ("+").move_to(P["sum"]); ml = circ("x", YELLOW).move_to(P["mul"]); lin = glyph_lin().move_to(P["lin"])
        gm = VGroup(Circle(.22, stroke_color=GREY_B, fill_color=GREY_D, fill_opacity=1, stroke_width=1.5), Text("g", font_size=18, font="DejaVu Sans")).move_to(P["gam"])
        ad = circ("+").move_to(P["add"])
        A = lambda a, b, **k: Arrow(a, b, buff=.05, stroke_width=3, color=GREY_B, max_tip_length_to_length_ratio=.15, **k)
        wires = VGroup(A(P["x"] + RIGHT * .2, P["ln"] + LEFT * .5),
                       A(P["ln"] + RIGHT * .5, [P["loc"][0] - .55, 1.5, 0]), A(P["ln"] + RIGHT * .5, [P["glo"][0] - .55, .2, 0]), A(P["ln"] + RIGHT * .5, [P["sil"][0] - .55, -1.6, 0]),
                       A([P["loc"][0] + .5, 1.5, 0], [P["sum"][0] - .25, .95, 0]), A([P["glo"][0] + .5, .2, 0], [P["sum"][0] - .22, .75, 0]),
                       A([P["sum"][0] + .25, .75, 0], [P["mul"][0] - .2, .15, 0]), A([P["sil"][0] + .5, -1.6, 0], [P["mul"][0] - .2, -.15, 0]),
                       A(P["mul"] + RIGHT * .27, P["lin"] + LEFT * .5), A(P["lin"] + RIGHT * .5, P["gam"] + LEFT * .24), A(P["gam"] + RIGHT * .24, P["add"] + LEFT * .27))
        skip = CurvedArrow([P["x"][0] + .1, .45, 0], [P["add"][0], .35, 0], angle=-TAU / 5, color=GREY_B, stroke_width=3).shift(UP * 2.0)
        skip = VMobject(stroke_color=GREY_B, stroke_width=3).set_points_as_corners([[P["x"][0], .5, 0], [P["x"][0], 2.5, 0], [P["add"][0], 2.5, 0], [P["add"][0], .3, 0]])
        skip_tip = Triangle(fill_color=GREY_B, fill_opacity=1, stroke_width=0).scale(.09).rotate(PI).move_to([P["add"][0], .33, 0])
        tags = VGroup(tag("LN").next_to(ln, DOWN, buff=.08), tag("3x3").next_to(loc, UP, buff=.08), tag("M").next_to(glo, DOWN, buff=.08), tag("SiLU").next_to(sil, DOWN, buff=.08),
                      tag("W").next_to(lin, DOWN, buff=.08), tag("skip", 16).move_to([-.5, 2.75, 0]))
        parts = [xt, ln, loc, glo, sil, sm, ml, lin, gm, ad]
        self.play(LaggedStart(*[FadeIn(p, scale=.8) for p in parts], lag_ratio=.12), run_time=2.2)
        self.play(Create(wires), Create(skip), FadeIn(skip_tip), FadeIn(tags), run_time=1.5)
        # token flowing through
        dot = Dot(color=YELLOW, radius=.11).move_to(P["x"])
        def path(*pts):
            m = VMobject(); m.set_points_as_corners([np.array(p, dtype=float) for p in pts]); return m
        self.add(dot)
        self.play(dot.animate.move_to(P["ln"]), run_time=.6)
        d1, d2, d3 = dot.copy(), dot.copy(), dot.copy(); self.add(d1, d2, d3)
        self.play(d1.animate.move_to(P["loc"]), d2.animate.move_to(P["glo"]), d3.animate.move_to(P["sil"]), FadeOut(dot), run_time=.8)
        self.play(d1.animate.move_to(P["sum"]), d2.animate.move_to(P["sum"]), run_time=.7)
        self.play(FadeOut(d2), d1.animate.move_to(P["mul"]), d3.animate.move_to(P["mul"]), run_time=.8)
        self.play(FadeOut(d3), d1.animate.move_to(P["add"]), run_time=1.2)
        sk = Dot(color=YELLOW, radius=.11).move_to(P["x"]); self.add(sk)
        self.play(MoveAlongPath(sk, skip), run_time=1.2); self.play(FadeOut(sk), FadeOut(d1), ad.animate.scale(1.3), run_time=.3); self.play(ad.animate.scale(1 / 1.3), run_time=.2)
        self.wait(.6)
        self.play(*[FadeOut(m) for m in self.mobjects])

        # ---------------------------------------------------------------- 4 pyramid
        def stack(g, sz, n, center, col):
            grp = VGroup()
            for k in range(n - 1, -1, -1):
                grp.add(cell_grid(g, sz, center=center + np.array([k * .13, k * .13, 0]), fill=col, op=.9, stroke=.4))
            return grp
        s0 = stack(16, 2.6, 2, LEFT * 4.8 + DOWN * .2, TEAL_E); s1 = stack(8, 1.8, 4, LEFT * .6 + DOWN * .2, TEAL_D); s2 = stack(4, 1.1, 7, RIGHT * 3.0 + DOWN * .2, TEAL_C)
        self.play(FadeIn(s0))
        # 2x2 merge animation
        top0 = s0[-1]; top1_center = LEFT * .6 + DOWN * .2
        hl = VGroup(*[top0[(6 + i) * 16 + (6 + j)].copy().set_fill(YELLOW, 1) for i in (0, 1) for j in (0, 1)]); self.play(FadeIn(hl))
        self.play(FadeIn(s1), run_time=.8)
        one = Square(1.8 / 8 * .95, fill_color=YELLOW, fill_opacity=1, stroke_width=0).move_to(s1[-1][3 * 8 + 3].get_center())
        cp = hl.copy(); self.add(cp); self.play(Transform(cp, one), run_time=.8); self.wait(.3)
        self.play(FadeOut(hl), FadeOut(cp))
        a1 = Arrow(s0.get_right(), s1.get_left(), buff=.25, color=GREY_B); a2 = Arrow(s1.get_right(), s2.get_left(), buff=.25, color=GREY_B)
        self.play(GrowArrow(a1)); self.play(FadeIn(s2)); self.play(GrowArrow(a2))
        self.wait(.4)
        # mean pooling -> vector -> class bars
        vec_cols = [RED_C, ORANGE, YELLOW, GREEN_C, BLUE_C, PURPLE_C, TEAL_C, PINK]
        vec = VGroup(*[Square(.22, fill_color=c, fill_opacity=1, stroke_width=0) for c in vec_cols]).arrange(DOWN, buff=0).move_to(RIGHT * 5.4 + UP * 2.2)
        self.play(*[FadeOut(m) for m in (s0, s1, a1, a2)], s2.animate.move_to(LEFT * 3.5 + DOWN * .2), run_time=.8)
        arr = Arrow(LEFT * 1.6, LEFT * .2, color=GREY_B); mean_ic = Text("mean", font_size=18, color=GREY_B, font="DejaVu Sans").next_to(arr, UP, buff=.05)
        self.play(GrowArrow(arr), FadeIn(mean_ic)); self.play(FadeIn(vec.move_to(RIGHT * 1.0)))
        arr2 = Arrow(RIGHT * 1.6, RIGHT * 2.8, color=GREY_B); self.play(GrowArrow(arr2))
        hs = [.4, .3, .5, 2.2, .35, .6, .25, .45]
        cls = VGroup(*[Rectangle(width=.3, height=h, fill_color=(YELLOW if i == 3 else GREY_B), fill_opacity=1, stroke_width=0).move_to([3.2 + i * .42, -1.6 + h / 2, 0]) for i, h in enumerate(hs)])
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in cls], lag_ratio=.08)); self.wait(1.2)
        self.play(*[FadeOut(m) for m in self.mobjects])

        # ---------------------------------------------------------------- 5 findings (pictures)
        # (a) the N x N mix  ==  9x9 stencil + one shared mean
        full = cell_grid(16, 2.8, center=LEFT * 4.6 + UP * 1.9, colors=[[COL[role(7, 7, r, c)] for c in range(16)] for r in range(16)], op=1, stroke=.2)
        eq = Text("=", font_size=44, font="DejaVu Sans").move_to(LEFT * 2.2 + UP * 1.9)
        st = cell_grid(9, 1.6, center=LEFT * 0.4 + UP * 1.9, colors=[[COL[role(4, 4, r, c)] for c in range(9)] for r in range(9)], op=1, stroke=.2)
        pl = Text("+", font_size=44, font="DejaVu Sans").move_to(RIGHT * 1.0 + UP * 1.9)
        mean = VGroup(Circle(.4, fill_color=COL["far"], fill_opacity=1, stroke_width=0), Text("mean", font_size=16, font="DejaVu Sans")).move_to(RIGHT * 2.1 + UP * 1.9)
        self.play(FadeIn(full), run_time=.8); self.play(FadeIn(eq), FadeIn(st), FadeIn(pl), FadeIn(mean), run_time=1.0)
        # (b) accuracy bars
        data = [("Baseline", 80.0, YELLOW), ("Model A", 72.0, "#4cc9f0"), ("Model B", 70.0, "#80ed99"), ("Model C", 65.0, "#b388ff")]  # illustrative numbers
        y0 = -3.1; sc = 1.9 / 80.0; x0 = -3.6
        base = Line([x0 - .5, y0, 0], [x0 + 5.2, y0, 0], color=GREY_B, stroke_width=2)
        self.play(Create(base))
        for i, (nm, v, c) in enumerate(data):
            h = v * sc * 1.0
            b = Rectangle(width=.9, height=h, fill_color=c, fill_opacity=1, stroke_width=0).move_to([x0 + i * 1.5, y0 + h / 2, 0])
            t1 = Text(f"{v:.1f}", font_size=20, font="DejaVu Sans").next_to(b, UP, buff=.06); t2 = tag(nm, 16).next_to(b, DOWN, buff=.06)
            self.play(GrowFromEdge(b, DOWN), FadeIn(t1), FadeIn(t2), run_time=.55)
        note = tag("illustrative numbers", 15).move_to([x0 + 2.25 + 1.5, -3.8, 0])
        self.play(FadeIn(note)); self.wait(2.5)
