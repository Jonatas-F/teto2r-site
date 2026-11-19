"""Ornamento "Planta áurea" da TETO.

Uma planta baixa desenhada sobre o retângulo áureo (H = 100, W = 100·φ).
Cada quadrado da série vira um cômodo; as paredes internas são as divisões
da espiral; as portas abrem em quarto de círculo (o arco do símbolo);
as janelas são vãos com caixilho de traço fino; as cotas marcam 1 : 0,618.

Saídas:
  brand/ornamentos/planta-aurea-ferro.svg   traço Ferro sobre fundo claro
  brand/ornamentos/planta-aurea-cal.svg     traço Cal sobre fundo escuro
  brand/ornamentos/planta-aurea-inline.svg  versão com currentColor e classes, para embutir e animar no site

Rodar de dentro de brand/:  python -I construcao/gerar_planta.py
"""
import os

PHI = (1 + 5 ** 0.5) / 2
H = 100.0
W = H * PHI
s1 = H              # quadrado A (estar)
s2 = H / PHI        # 61,8  quadrado B (quarto)
s3 = s2 / PHI       # 38,2  quadrado C
s4 = s3 / PHI       # 23,6  quadrado D (banho)
s5 = s4 / PHI       # 14,6  quadrado E

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "ornamentos")


def n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def seg(x1, y1, x2, y2):
    return f"M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}"


def arc(x1, y1, r, x2, y2, sweep=1):
    return f"M{n(x1)} {n(y1)}A{n(r)} {n(r)} 0 0 {sweep} {n(x2)} {n(y2)}"


def build():
    ext, inn, door, win, spiral, cota = [], [], [], [], [], []

    # Paredes externas (com vãos de porta e janela)
    jan_topo = (s1 * 0.2, s1 * 0.2 + s2)            # janela grande do estar: largura s2
    ext += [seg(0, 0, jan_topo[0], 0), seg(jan_topo[1], 0, W, 0)]
    jan_dir = (s2 * 0.25, s2 * 0.25 + s3)           # janela do quarto: largura s3
    ext += [seg(W, 0, W, jan_dir[0]), seg(W, jan_dir[1], W, H)]
    porta = (s3, s3 + s5 * 0.8)                     # porta de entrada no estar
    ext += [seg(W, H, porta[1], H), seg(porta[0], H, 0, H)]
    jan_esq = (s3, s3 + s4)                         # janela lateral do estar
    ext += [seg(0, H, 0, jan_esq[1]), seg(0, jan_esq[0], 0, 0)]

    # Paredes internas = divisões da série áurea, com vãos de porta
    pa = (s4 * 0.8, s4 * 0.8 + s5 * 0.62)           # porta estar -> quarto em x = 100
    inn += [seg(s1, 0, s1, pa[0]), seg(s1, pa[1], s1, H)]
    pb = (s1 + s3 + s5 * 0.4, s1 + s3 + s5 * 0.4 + s5 * 0.62)  # porta quarto -> C em y = s2
    inn += [seg(s1, s2, pb[0], s2), seg(pb[1], s2, W, s2)]
    inn += [seg(s1 + s4, s2, s1 + s4, H)]           # C | D
    inn += [seg(s1, s2 + s5, s1 + s4, s2 + s5)]     # D sobre E
    inn += [seg(s1 + s5, s2, s1 + s5, s2 + s5)]     # E

    # Portas: folha + giro em quarto de círculo (o arco do símbolo)
    w = porta[1] - porta[0]
    door += [seg(porta[0], H, porta[0], H - w), arc(porta[0], H - w, w, porta[1], H)]
    w = pa[1] - pa[0]
    door += [seg(s1, pa[0], s1 + w, pa[0]), arc(s1 + w, pa[0], w, s1, pa[1])]
    w = pb[1] - pb[0]
    door += [seg(pb[1], s2, pb[1], s2 + w), arc(pb[1], s2 + w, w, pb[0], s2)]

    # Janelas: caixilho de duas linhas finas no vão
    e = 0.9
    win += [seg(jan_topo[0], -e, jan_topo[1], -e), seg(jan_topo[0], e, jan_topo[1], e)]
    win += [seg(W - e, jan_dir[0], W - e, jan_dir[1]), seg(W + e, jan_dir[0], W + e, jan_dir[1])]
    win += [seg(-e, jan_esq[0], -e, jan_esq[1]), seg(e, jan_esq[0], e, jan_esq[1])]

    # Espiral áurea: um quarto de círculo por quadrado
    spiral += [
        arc(0, H, s1, s1, 0),
        arc(s1, 0, s2, W, s2),
        arc(W, s2, s3, s1 + s4, H),
        arc(s1 + s4, H, s4, s1, s2 + s5),
        arc(s1, s2 + s5, s5, s1 + s5, s2),
    ]

    # Cotas: 1 : 0,618 embaixo e 0,618 : 0,382 à direita, com traço de 45 graus
    yc, xc, t = H + 9, W + 9, 2.2
    cota += [seg(0, yc, W, yc), seg(xc, 0, xc, H)]
    for x in (0, s1, W):
        cota += [seg(x - t, yc + t, x + t, yc - t), seg(x, H + 3, x, yc + 3)]
    for y in (0, s2, H):
        cota += [seg(xc - t, y + t, xc + t, y - t), seg(W + 3, y, xc + 3, y)]

    return {"ext": ext, "inn": inn, "door": door, "win": win, "spiral": spiral, "cota": cota}


ESTILO = {  # espessura em px (não escala) e opacidade
    "ext": (2.5, 1.0),
    "inn": (1.25, 0.85),
    "door": (1.0, 0.7),
    "win": (1.0, 0.7),
    "spiral": (1.0, 1.0),
    "cota": (1.0, 0.55),
}
VIEWBOX = f"-4 -4 {n(W + 18)} {n(H + 18)}"


def estatico(cor, cor_espiral, opac):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEWBOX}"><title>Planta áurea TETO</title>',
           f'<g fill="none" stroke-linecap="square" opacity="{opac}">']
    for k, paths in build().items():
        sw, op = ESTILO[k]
        c = cor_espiral if k == "spiral" else cor
        out.append(f'<path d="{"".join(paths)}" stroke="{c}" stroke-opacity="{op}" stroke-width="{sw}" vector-effect="non-scaling-stroke"/>')
    out.append("</g></svg>")
    return "".join(out)


def inline():
    """Uma linha por traço, com pathLength=1, para o site animar o desenho na rolagem."""
    out = [f'<svg class="planta" viewBox="{VIEWBOX}" aria-hidden="true" focusable="false">']
    ordem = 0
    for k, paths in build().items():
        sw, op = ESTILO[k]
        out.append(f'<g class="planta__{k}" stroke-width="{sw}" stroke-opacity="{op}">')
        for d in paths:
            out.append(f'<path d="{d}" pathLength="1" style="--o:{ordem}"/>')
            ordem += 1
        out.append("</g>")
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "planta-aurea-ferro.svg"), "w", encoding="utf-8") as f:
        f.write(estatico("#171716", "#3B7A2A", 0.32))
    with open(os.path.join(OUT, "planta-aurea-cal.svg"), "w", encoding="utf-8") as f:
        f.write(estatico("#F5F0E6", "#8DC63F", 0.4))
    with open(os.path.join(OUT, "planta-aurea-inline.svg"), "w", encoding="utf-8") as f:
        f.write(inline())
    print(f"W={W:.3f} quadrados: {s1:.1f} {s2:.1f} {s3:.1f} {s4:.1f} {s5:.1f}")
