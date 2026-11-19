# -*- coding: utf-8 -*-
"""
Gera a marca TETO a partir dos círculos da série áurea.

Tudo sai daqui: SVGs do símbolo e das assinaturas, PNGs, favicon, avatar,
ornamentos, imagens dos testes, o estudo de evolução e os diagramas
injetados no manual (brand/index.html, entre marcadores <!-- gerar:... -->).

Uso, de dentro de brand/:
    python -I construcao/gerar_marca.py

Trocar a fonte do letreiro sem editar o script:
    python -I construcao/gerar_marca.py \
        --fonte-letreiro _fontes/outra/Outra.ttf --eixos-letreiro "wght=800" \
        --fonte-descritor _fontes/outra/Outra.ttf --eixos-descritor "wght=500" \
        --track-letreiro 0.01 --track-descritor 0.06
Fonte variável: os eixos são instanciados com fontTools. Fonte estática:
passe --eixos-... "" (vazio). Caminhos relativos partem de brand/.

Precisa de: fontTools, uharfbuzz, shapely, Pillow.
"""
import argparse
import io
import math
import os
import re
import sys

BRAND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ======================================================================
# CONFIGURAÇÃO DO LETREIRO (troque aqui ou pela linha de comando)
# ======================================================================
FONTE_LETREIRO = os.path.join(BRAND, "_fontes", "archivo", "Archivo-wdth-wght.ttf")
EIXOS_LETREIRO = {"wdth": 75, "wght": 800}
TRACK_LETREIRO = 0.01          # em em
FONTE_DESCRITOR = FONTE_LETREIRO
EIXOS_DESCRITOR = {"wdth": 100, "wght": 600}
TRACK_DESCRITOR = 0.06         # em em
TEXTO_LETREIRO = "TETO"
TEXTO_DESCRITOR = ("ARQUITETURA", "SUSTENTÁVEL")
GLIFO_VERSAL = "H"             # glifo que define a altura de versal
# ======================================================================

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
import uharfbuzz as hb

OUT_LOGO = os.path.join(BRAND, "logo")
OUT_IMG = os.path.join(BRAND, "img")
OUT_ORN = os.path.join(BRAND, "ornamentos")

# ----------------------------------------------------------------------
# Série
# ----------------------------------------------------------------------
PHI = (1 + 5 ** 0.5) / 2


def f(n):
    return PHI ** n


SERIE = {n: f(n) for n in range(-3, 8)}

# ----------------------------------------------------------------------
# Cores
# ----------------------------------------------------------------------
GRAMA = "#3B7A2A"
GRAMA_P = "#23501A"
FERRO = "#171716"
CAL = "#F5F0E6"
CAL_E = "#EBE3D3"
BRANCO = "#FFFFFF"
BROTO = "#8DC63F"
TELHA = "#B04E28"
PEDRA = "#5E5A52"

# ----------------------------------------------------------------------
# Geometria do símbolo (unidade u, eixo y para baixo, centro do arco em 0,0)
# ----------------------------------------------------------------------
R = f(5)            # raio externo do arco                 11,090 u
r = f(4)            # raio interno do arco                  6,854 u
E = R - r           # espessura do arco e da viga = φ³      4,236 u
OS = f(-2)          # compensação ótica das pontas          0,382 u
A = f(3) + OS       # semidiagonal do losango               4,618 u
C = (r, r)          # centro do losango: canto do quadrado que circunscreve o vazio
VAO = r - A         # vão ponta do losango / corte do arco = φ² − φ⁻² = √5
# Variante do símbolo.
#   "anel": anel de três quartos + losango. É a versão aprovada e o padrão.
#   "viga" e "t": estudos de evolução reprovados pelo cliente, mantidos só como registro.
SIMBOLO = "anel"
PL = E              # largura do pilar (só na variante "t")
PX0, PX1 = r - PL / 2, r + PL / 2
PY1 = 0.0
XV = R + OS         # fim da viga (só nas variantes de estudo)


def _definir_variante(v):
    global SIMBOLO, XV, X1, LARG
    SIMBOLO = v
    XV = 2 * r if v == "t" else R + OS
    X1 = max(XV, C[0] + A)
    LARG = X1 - X0
PROTECAO = E
X0, Y0 = -R, -R
X1, Y1 = max(XV, C[0] + A), C[1] + A
LARG = X1 - X0      # R + 2r
ALT = Y1 - Y0
S = 10.0            # 1 u = 10 unidades de SVG


def n(v):
    s = ("%.3f" % (v * S)).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def arco_d(dx=0.0, dy=0.0):
    """Parte verde. Variante anel: 3/4 de anel, de (R, 0) contornando por cima e pela
    esquerda até (0, R), cortes radiais nos dois eixos. Estudos: meio anel à esquerda."""
    if SIMBOLO == "anel":
        return (f"M{n(R+dx)} {n(dy)}A{n(R)} {n(R)} 0 1 0 {n(dx)} {n(R+dy)}"
                f"L{n(dx)} {n(r+dy)}A{n(r)} {n(r)} 0 1 1 {n(r+dx)} {n(dy)}Z")
    return (f"M{n(dx)} {n(-R+dy)}A{n(R)} {n(R)} 0 0 0 {n(dx)} {n(R+dy)}"
            f"L{n(dx)} {n(r+dy)}A{n(r)} {n(r)} 0 0 1 {n(dx)} {n(-r+dy)}Z")


def t_d(dx=0.0, dy=0.0):
    """A parte preta: viga de y = −R a y = −r, de x = 0 a XV (e o pilar, na variante "t")."""
    if SIMBOLO == "t":
        return (f"M{n(dx)} {n(-R+dy)}H{n(XV+dx)}V{n(-r+dy)}H{n(PX1+dx)}V{n(PY1+dy)}"
                f"H{n(PX0+dx)}V{n(-r+dy)}H{n(dx)}Z")
    return f"M{n(dx)} {n(-R+dy)}H{n(XV+dx)}V{n(-r+dy)}H{n(dx)}Z"


def uniao_d(dx=0.0, dy=0.0):
    """Arco + viga num contorno só (estudos). Na variante anel é o próprio anel."""
    if SIMBOLO == "anel":
        return arco_d(dx, dy)
    pilar = (f"H{n(PX0+dx)}V{n(PY1+dy)}H{n(PX1+dx)}V{n(-r+dy)}" if SIMBOLO == "t" else "")
    return (f"M{n(XV+dx)} {n(-R+dy)}H{n(dx)}A{n(R)} {n(R)} 0 0 0 {n(dx)} {n(R+dy)}"
            f"L{n(dx)} {n(r+dy)}A{n(r)} {n(r)} 0 0 1 {n(dx)} {n(-r+dy)}{pilar}H{n(XV+dx)}Z")


def losango_d(dx=0.0, dy=0.0, c=C, a=A):
    cx, cy = c[0] + dx, c[1] + dy
    return (f"M{n(cx)} {n(cy-a)}L{n(cx+a)} {n(cy)}"
            f"L{n(cx)} {n(cy+a)}L{n(cx-a)} {n(cy)}Z")


# ----------------------------------------------------------------------
# Polígonos densos
# ----------------------------------------------------------------------
def disco(c, rad, res=512):
    return Point(c).buffer(rad, resolution=res)


def los_poly(c, a):
    x, y = c
    return Polygon([(x, y - a), (x + a, y), (x, y + a), (x - a, y)])


def geometria():
    if SIMBOLO == "anel":
        arco = disco((0, 0), R).difference(disco((0, 0), r)).difference(box(0, 0, 100, 100))
        return {"arco": arco, "viga": Polygon(), "uniao": arco, "losango": los_poly(C, A)}
    arco = disco((0, 0), R).difference(disco((0, 0), r)).difference(box(0, -100, 100, 100))
    viga = box(0, -R, XV, -r)
    if SIMBOLO == "t":
        viga = unary_union([viga, box(PX0, -r, PX1, PY1)])
    return {"arco": arco, "viga": viga, "uniao": unary_union([arco, viga]),
            "losango": los_poly(C, A)}


def geometria_opcoes():
    """Estudo de evolução em P&B. Rodada 1: um elemento somado ao anel.
    Rodada 2: a parte preta vira T (barra + pilar) e três desfechos para o pé."""
    anel34 = disco((0, 0), R).difference(disco((0, 0), r)).difference(box(0, 0, 100, 100))
    meio = disco((0, 0), R).difference(disco((0, 0), r)).difference(box(0, -100, 100, 100))
    L = los_poly(C, A)
    barra = box(0, -R, 2 * r, -r)
    topo_los = C[1] - A
    pilar = lambda y1: box(PX0, -r, PX1, y1)
    return {
        "empena": unary_union([anel34, L.difference(box(0, r - f(1) / 2, 100, r + f(1) / 2))]),
        "viga": unary_union([meio, box(0, -R, R + OS, -r), L]),
        "copa": unary_union([anel34, disco((0, 0), f(3)).difference(disco((0, 0), f(2))).difference(box(0, 0, 100, 100)), L]),
        # a) prumo: o pilar entra no losango até a largura do pilar
        "prumo": unary_union([meio, barra, pilar(topo_los + PL / 2), L]),
        # b) junta de E/φ³ = φ⁰ entre o pilar e a ponta do losango
        "junta": unary_union([meio, barra, pilar(topo_los - E / f(3)), L]),
        # c) pilar de comprimento φ⁴ até o eixo; losango solto a √5
        "pilar": unary_union([meio, barra, pilar(PY1), L]),
    }


def hexrgba(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def raster(px, camadas, fundo=(0, 0, 0, 0), quadro=None, ss=16):
    """camadas: lista (geometria, RGBA). quadro: (x0, y0, w, h) em u."""
    if quadro is None:
        quadro = (X0, Y0, LARG, ALT)
    qx, qy, qw, qh = quadro
    W = px * ss
    H = round(px * qh / qw) * ss
    sc = W / qw
    im = Image.new("RGBA", (W, H), fundo)
    for geo, cor in camadas:
        lay = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(lay)
        for p in getattr(geo, "geoms", [geo]):
            d.polygon([((x - qx) * sc, (y - qy) * sc) for x, y in p.exterior.coords], fill=255)
            for h in p.interiors:
                d.polygon([((x - qx) * sc, (y - qy) * sc) for x, y in h.coords], fill=0)
        im.paste(Image.new("RGBA", (W, H), cor), (0, 0), lay)
    return im.resize((W // ss, H // ss), Image.BOX)


def camadas_cor(g, arco=GRAMA, viga=FERRO, los=FERRO):
    if SIMBOLO == "anel":
        return [(g["arco"], hexrgba(arco)), (g["losango"], hexrgba(los))]
    return [(g["uniao"], hexrgba(viga)), (g["arco"], hexrgba(arco)), (g["losango"], hexrgba(los))]


# ----------------------------------------------------------------------
# Verificação
# ----------------------------------------------------------------------
def nome_serie(v, tol=1e-9):
    for k, s in SERIE.items():
        if abs(v - s) < tol:
            return "φ^%d" % k
    return None


def verificar():
    linhas = []
    ok = True

    def item(cond, txt):
        nonlocal ok
        ok = ok and cond
        linhas.append(("OK   " if cond else "FALHA") + "  " + txt)

    linhas += [f"Verificação geométrica do símbolo TETO (variante {SIMBOLO})",
               "Unidade u. Série φ^n, n de -3 a 7.", ""]
    if SIMBOLO == "anel":
        for nome, rad in (("arco externo", R), ("arco interno", r)):
            item(nome_serie(rad) is not None, f"{nome}: raio {rad:.3f} u = {nome_serie(rad)}")
        item(abs(E - f(3)) < 1e-9, f"espessura do anel R − r = {E:.3f} u = φ^3")
        for (p_, q_) in (((0, r), (0, R)), ((r, 0), (R, 0))):
            item(abs(p_[0] * q_[1] - p_[1] * q_[0]) < 1e-9, f"corte de {p_[0]:.3f},{p_[1]:.3f} a {q_[0]:.3f},{q_[1]:.3f} é radial: encontra os arcos a 90° (canto intencional)")
        item(nome_serie(A - OS) is not None, f"semidiagonal do losango sem correção = {A-OS:.3f} u = φ^3")
        item(nome_serie(OS) is not None, f"compensação ótica das pontas = {OS:.3f} u = φ^-2")
        item(abs((r + f(3)) - R) < 1e-9, "pilha que fecha: r + φ^3 = R (pontas do losango no quadrado do anel antes da correção)")
        item(abs(VAO - 5 ** 0.5) < 1e-9, f"vão ponta do losango / corte do anel = φ² − φ⁻² = √5 = {VAO:.3f} u")
        item(abs(C[0] - r) < 1e-12, "ponta de cima do losango alinhada ao canto interno do corte horizontal (x = r)")
        g = geometria()
        dmin = g["arco"].distance(g["losango"])
        item(abs(dmin - VAO) < 1e-3, f"menor distância anel/losango medida em polígono denso = {dmin:.3f} u")
        cmds = set(re.findall(r"[A-Za-z]", arco_d() + losango_d()))
        item(cmds <= set("MALZ"), "sem Bézier: contorno só com " + ", ".join(sorted(cmds)))
        linhas.append("")
        linhas.append(f"caixa do símbolo: {LARG:.3f} × {ALT:.3f} u")
        linhas.append(f"área de proteção: {PROTECAO:.3f} u (φ^3, espessura do anel)")
        linhas.append(f"menor vão: {VAO:.3f} u → altura mínima com vão ≥ 1 px = {ALT/VAO:.1f} px; impressão (0,25 mm): {ALT/VAO*0.25:.2f} mm")
        return ok, linhas
    for nome, rad in (("arco externo", R), ("arco interno", r)):
        item(nome_serie(rad) is not None, f"{nome}: raio {rad:.3f} u = {nome_serie(rad)}")
    item(abs(E - f(3)) < 1e-9, f"espessura do arco R − r = {E:.3f} u = φ^3")
    for nome, rad in (("de cima", R), ("de baixo", r)):
        # contato (0, −rad): está no círculo e o raio até ele é perpendicular à face horizontal
        contato = (0.0, -rad)
        no_circulo = abs(math.hypot(*contato) - rad) < 1e-12
        perpendicular = abs(contato[0] * 1.0 + contato[1] * 0.0) < 1e-12
        item(no_circulo and perpendicular, f"face {nome} da viga (y = −{rad:.3f}) tangente ao círculo {nome_serie(rad)} em (0, −{rad:.3f})")
    item(abs(R - r - E) < 1e-12, f"altura da viga = espessura do arco = φ^3 = {E:.3f} u")
    if SIMBOLO == "t":
        item(abs((PX0 + PX1) / 2 - C[0]) < 1e-12, f"pilar centrado em x = r = {r:.3f} u, o mesmo eixo do losango")
        item(abs((PY1 + r) - f(4)) < 1e-12, "pilar de comprimento φ^4; pilar + barra = φ^5")
        item(abs((C[1] - A) - PY1 - VAO) < 1e-12, "vão pé do pilar / losango = √5")
    else:
        item(abs(XV - (C[0] + A)) < 1e-12, f"fim da viga x = R + φ⁻² = {XV:.3f} u, alinhado à ponta direita do losango")
    item(True, "corte de baixo do arco é radial (x = 0): encontra os dois arcos a 90°, canto intencional")
    item(True, "fim da viga é reta vertical: canto de 90°, intencional")
    item(nome_serie(A - OS) is not None, f"semidiagonal do losango sem correção = {A-OS:.3f} u = φ^3")
    item(nome_serie(OS) is not None, f"compensação ótica das pontas = {OS:.3f} u = φ^-2")
    item(abs((r + f(3)) - R) < 1e-9, "pilha que fecha: r + φ^3 = R")
    item(abs(VAO - 5 ** 0.5) < 1e-9, f"vão ponta esquerda do losango / corte do arco = φ² − φ⁻² = √5 = {VAO:.3f} u")
    g = geometria()
    dmin = g["uniao"].distance(g["losango"])
    item(abs(dmin - VAO) < 1e-3, f"menor distância arco+viga / losango medida em polígono denso = {dmin:.3f} u")
    cmds = set(re.findall(r"[A-Za-z]", uniao_d() + arco_d() + losango_d()))
    item(cmds <= set("MAHVLZ"), "sem Bézier: contorno só com " + ", ".join(sorted(cmds)))
    linhas.append("")
    linhas.append(f"caixa do símbolo: {LARG:.3f} × {ALT:.3f} u")
    linhas.append(f"área de proteção: {PROTECAO:.3f} u (φ^3)")
    vmin = min(VAO, E)
    linhas.append(f"menor vão: {vmin:.3f} u → altura mínima com vão ≥ 1 px = {ALT/vmin:.1f} px; impressão (0,25 mm): {ALT/vmin*0.25:.2f} mm")
    return ok, linhas


# ----------------------------------------------------------------------
# Texto em contornos (parametrizado)
# ----------------------------------------------------------------------
_inst = {}


def instancia(caminho, eixos):
    k = (caminho, tuple(sorted((eixos or {}).items())))
    if k not in _inst:
        fv = TTFont(caminho)
        if "fvar" in fv and eixos:
            tags = {a.axisTag for a in fv["fvar"].axes}
            loc = {t: v for t, v in eixos.items() if t in tags}
            fv = instancer.instantiateVariableFont(fv, loc)
        b = io.BytesIO()
        fv.save(b)
        data = b.getvalue()
        _inst[k] = (TTFont(io.BytesIO(data)), data)
    return _inst[k]


def texto(txt, caminho, eixos, versal, track_em=0.0):
    """(d, largura) com linha de base em y=0 e x começando na tinta do 1º glifo."""
    ft, data = instancia(caminho, eixos)
    gs = ft.getGlyphSet()
    cmap = ft.getBestCmap()
    bp = BoundsPen(gs)
    gs[cmap[ord(GLIFO_VERSAL)]].draw(bp)
    sc = versal / bp.bounds[3]
    upm = ft["head"].unitsPerEm
    font = hb.Font(hb.Face(data))
    buf = hb.Buffer()
    buf.add_str(txt)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": False})
    order = ft.getGlyphOrder()
    x = 0.0
    glifos = []
    for i, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
        glifos.append((order[info.codepoint], x + pos.x_offset))
        x += pos.x_advance + (track_em * upm if i < len(buf.glyph_infos) - 1 else 0)
    xmin, xmax = 1e9, -1e9
    for gn, gx in glifos:
        b = BoundsPen(gs)
        gs[gn].draw(b)
        if b.bounds:
            xmin, xmax = min(xmin, gx + b.bounds[0]), max(xmax, gx + b.bounds[2])
    partes = []
    for gn, gx in glifos:
        pen = SVGPathPen(gs, lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
        gs[gn].draw(TransformPen(pen, (sc * S, 0, 0, -sc * S, (gx - xmin) * sc * S, 0)))
        if pen.getCommands():
            partes.append(pen.getCommands())
    return " ".join(partes), (xmax - xmin) * sc


def mover_d(d, dx, dy):
    tok = re.findall(r"[MLQCZHV]|-?\d*\.?\d+(?:e-?\d+)?", d)
    out, cmd, par = "", None, 0
    for t in tok:
        if t.isalpha():
            cmd, par = t, 0
            out += t
            continue
        v = float(t)
        if cmd == "H":
            v += dx
        elif cmd == "V":
            v += dy
        else:
            v += dx if par % 2 == 0 else dy
            par += 1
        s = ("%.2f" % v).rstrip("0").rstrip(".")
        out += s if out[-1:].isalpha() else " " + s
    return out


def letreiro(versal):
    return texto(TEXTO_LETREIRO, FONTE_LETREIRO, EIXOS_LETREIRO, versal, TRACK_LETREIRO)


def descritor(i, versal):
    return texto(TEXTO_DESCRITOR[i], FONTE_DESCRITOR, EIXOS_DESCRITOR, versal, TRACK_DESCRITOR)


# ----------------------------------------------------------------------
# Assinaturas
# ----------------------------------------------------------------------
def assinatura_horizontal():
    """Símbolo + letreiro (versal φ⁵) + fio + descritor em duas linhas (φ³ + φ² + φ³ = φ⁵)."""
    vers = R
    d_t, w_t = letreiro(vers)
    d_1, w1 = descritor(0, f(3))
    d_2, w2 = descritor(1, f(3))
    x_t = (R if SIMBOLO == "anel" else X1) + f(4)   # no anel, φ⁴ medido a partir do raio externo
    x_fio = x_t + w_t + f(3)
    x_d = x_fio + f(0) + f(3)
    topo, base = -vers / 2, vers / 2
    txt = [mover_d(d_t, x_t * S, base * S), mover_d(d_1, x_d * S, (topo + f(3)) * S),
           mover_d(d_2, x_d * S, base * S), f"M{n(x_fio)} {n(topo)}h{n(f(0))}v{n(vers)}h{n(-f(0))}Z"]
    x_fim = x_d + max(w1, w2)
    med = dict(x_teto=x_t, w_teto=w_t, x_fio=x_fio, x_desc=x_d, w_desc=max(w1, w2), x_fim=x_fim)
    return txt, (X0, Y0, x_fim - X0, ALT), med


def assinatura_vertical():
    d_t, w_t = letreiro(f(5))
    d_1, w1 = descritor(0, f(2))
    d_2, w2 = descritor(1, f(2))
    larg = max(w_t, w1, w2, LARG)
    cx = larg / 2
    sdx, sdy = cx - LARG / 2 - X0, -Y0
    y_t = ALT + f(4) + f(5)
    y_1 = y_t + f(3) + f(2)
    y_2 = y_1 + f(1) + f(2)
    txt = [mover_d(d_t, (cx - w_t / 2) * S, y_t * S), mover_d(d_1, (cx - w1 / 2) * S, y_1 * S),
           mover_d(d_2, (cx - w2 / 2) * S, y_2 * S)]
    return (sdx, sdy), txt, (0, 0, larg, y_2)


def svg(viewbox, corpo, titulo, extra=""):
    x, y, w, h = viewbox
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s %s %s %s"%s role="img" aria-labelledby="t">'
            '<title id="t">%s</title>%s</svg>\n' % (n(x), n(y), n(w), n(h), extra, titulo, corpo))


# arco, viga, losango, letreiro
VARIANTES = {
    "": (GRAMA, FERRO, FERRO, FERRO),
    "-preto": (FERRO, FERRO, FERRO, FERRO),
    "-branco": (BRANCO, BRANCO, BRANCO, BRANCO),
    "-negativo": (BROTO, BRANCO, BRANCO, BRANCO),
}


def corpo_simbolo(ca, cv, cl, dx=0.0, dy=0.0):
    if SIMBOLO == "anel":
        return f'<path fill="{ca}" d="{arco_d(dx, dy)}"/><path fill="{cl}" d="{losango_d(dx, dy)}"/>'
    if ca == cv:
        return f'<path fill="{cv}" d="{uniao_d(dx, dy)}"/><path fill="{cl}" d="{losango_d(dx, dy)}"/>'
    # a união vai por baixo para a emenda arco/viga não deixar fio de fundo
    return (f'<path fill="{cv}" d="{uniao_d(dx, dy)}"/><path fill="{ca}" d="{arco_d(dx, dy)}"/>'
            f'<path fill="{cl}" d="{losango_d(dx, dy)}"/>')


def escrever_logos():
    os.makedirs(OUT_LOGO, exist_ok=True)
    gerados = []
    tit = "TETO Arquitetura Sustentável"
    for suf, (ca, cv, cl, ct) in VARIANTES.items():
        nome = f"teto-simbolo{suf}.svg"
        open(os.path.join(OUT_LOGO, nome), "w", encoding="utf-8").write(
            svg((X0, Y0, LARG, ALT), corpo_simbolo(ca, cv, cl), tit))
        gerados.append(nome)
    txt, caixa, med = assinatura_horizontal()
    for suf, (ca, cv, cl, ct) in VARIANTES.items():
        nome = f"teto-horizontal{suf}.svg"
        corpo = corpo_simbolo(ca, cv, cl) + f'<path fill="{ct}" d="{" ".join(txt)}"/>'
        open(os.path.join(OUT_LOGO, nome), "w", encoding="utf-8").write(svg(caixa, corpo, tit))
        gerados.append(nome)
    (sdx, sdy), txtv, caixav = assinatura_vertical()
    for suf, (ca, cv, cl, ct) in VARIANTES.items():
        nome = f"teto-vertical{suf}.svg"
        corpo = corpo_simbolo(ca, cv, cl, sdx, sdy) + f'<path fill="{ct}" d="{" ".join(txtv)}"/>'
        open(os.path.join(OUT_LOGO, nome), "w", encoding="utf-8").write(svg(caixav, corpo, tit))
        gerados.append(nome)
    # favicon: símbolo sobre placa Cal, margem φ¹
    m = f(1)
    lado = LARG + 2 * m
    corpo = (f'<rect x="{n(X0-m)}" y="{n(Y0-m)}" width="{n(lado)}" height="{n(lado)}" rx="{n(f(1))}" fill="{CAL}"/>'
             + corpo_simbolo(GRAMA, FERRO, FERRO))
    open(os.path.join(OUT_LOGO, "favicon.svg"), "w", encoding="utf-8").write(svg((X0 - m, Y0 - m, lado, lado), corpo, "TETO"))
    gerados.append("favicon.svg")
    # avatar: símbolo em disco Cal, margem φ⁴ (cabe no recorte circular das redes)
    m = f(4)
    lado = LARG + 2 * m
    cx, cy = X0 + LARG / 2, Y0 + ALT / 2
    corpo = (f'<rect x="{n(X0-m)}" y="{n(Y0-m)}" width="{n(lado)}" height="{n(lado)}" fill="{CAL}"/>'
             + corpo_simbolo(GRAMA, FERRO, FERRO))
    open(os.path.join(OUT_LOGO, "teto-avatar.svg"), "w", encoding="utf-8").write(svg((X0 - m, Y0 - m, lado, lado), corpo, tit))
    gerados.append("teto-avatar.svg")
    return gerados, med


def escrever_pngs():
    g = geometria()
    cor = camadas_cor(g)
    raster(512, cor).save(os.path.join(OUT_LOGO, "teto-simbolo-512.png"))
    raster(32, cor).save(os.path.join(OUT_LOGO, "teto-simbolo-32.png"))
    m = f(1)
    lado = LARG + 2 * m
    q = (X0 - m, Y0 - m, lado, lado)
    for px, destino in ((64, os.path.join(OUT_LOGO, "favicon.png")), (16, os.path.join(OUT_IMG, "testes", "favicon-16.png"))):
        ss = 16
        base = Image.new("RGBA", (px * ss, px * ss), (0, 0, 0, 0))
        ImageDraw.Draw(base).rounded_rectangle((0, 0, px * ss - 1, px * ss - 1), radius=f(1) / lado * px * ss, fill=hexrgba(CAL))
        base = base.resize((px, px), Image.BOX)
        base.alpha_composite(raster(px, cor, quadro=q))
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        base.save(destino)
    m = f(4)
    lado = LARG + 2 * m
    av = raster(1080, cor, fundo=hexrgba(CAL), quadro=(X0 - m, Y0 - m, lado, lado))
    av.save(os.path.join(OUT_LOGO, "teto-avatar-1080.png"))


def escrever_testes():
    t = os.path.join(OUT_IMG, "testes")
    os.makedirs(t, exist_ok=True)
    g = geometria()
    cor = camadas_cor(g)
    preto = camadas_cor(g, FERRO, FERRO, FERRO)
    claro = camadas_cor(g, CAL, CAL, CAL)
    for px in (16, 32, 64, 512):
        im = Image.new("RGBA", (px, px), hexrgba(CAL))
        im.alpha_composite(raster(px, cor))
        im.save(os.path.join(t, f"simbolo-{px}.png"))
        im = Image.new("RGBA", (px, px), hexrgba(FERRO))
        im.alpha_composite(raster(px, claro))
        im.save(os.path.join(t, f"simbolo-{px}-invertido.png"))
    px, pad = 400, 4
    q = (X0 - pad, Y0 - pad, LARG + 2 * pad, ALT + 2 * pad)
    im = Image.new("RGBA", (px, px), (255, 255, 255, 255))
    im.alpha_composite(raster(px, preto, quadro=q))
    im.convert("L").filter(ImageFilter.GaussianBlur(px * 0.08 * ALT / q[3])).save(os.path.join(t, "desfoque.png"))
    # silhueta: arco com o vazio preenchido + viga + losango
    if SIMBOLO == "anel":
        silh = unary_union([disco((0, 0), R).difference(box(0, 0, 100, 100)), g["losango"], box(0, 0, r, r)])
    else:
        silh = unary_union([disco((0, 0), R).difference(box(0, -100, 100, 100)), g["viga"], g["losango"]])
    im = Image.new("RGBA", (px, px), (255, 255, 255, 255))
    im.alpha_composite(raster(px, [(silh, hexrgba(FERRO))], quadro=q))
    im.convert("L").save(os.path.join(t, "silhueta.png"))


# ----------------------------------------------------------------------
# Diagramas para o manual
# ----------------------------------------------------------------------
def vb(c):
    return " ".join(n(v) for v in c)


def _cota(L, x1, y1, x2, y2, txt, tx, ty, anc="middle"):
    L.append(f'<path class="cota" d="M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}"/>')
    for (x, y) in ((x1, y1), (x2, y2)):
        L.append(f'<path class="cota" d="M{n(x-0.45)} {n(y+0.45)}L{n(x+0.45)} {n(y-0.45)}"/>')
    L.append(f'<text class="rot" x="{n(tx)}" y="{n(ty)}" text-anchor="{anc}">{txt}</text>')


def grade_base(L, eixo_diag=True):
    L.append(f'<rect class="g g-fina" x="{n(-R)}" y="{n(-R)}" width="{n(2*R)}" height="{n(2*R)}"/>')
    L.append(f'<rect class="g g-fina" x="{n(-r)}" y="{n(-r)}" width="{n(2*r)}" height="{n(2*r)}"/>')
    d = f'M{n(-R-3)} 0H{n(R+3)}M0 {n(-R-3)}V{n(R+3)}'
    if eixo_diag:
        d += f'M{n(-R*0.75)} {n(-R*0.75)}L{n(R+2)} {n(R+2)}'
    L.append(f'<path class="g g-eixo" d="{d}"/>')
    L.append(f'<circle class="g g-forte" cx="0" cy="0" r="{n(R)}"/>')
    L.append(f'<circle class="g g-forte" cx="0" cy="0" r="{n(r)}"/>')
    L.append(f'<circle class="g g-forte" cx="{n(C[0])}" cy="{n(C[1])}" r="{n(f(3))}"/>')
    for (x, y) in ((0, 0), C):
        L.append(f'<circle class="ponto" cx="{n(x)}" cy="{n(y)}" r="{n(0.32)}"/>')


def diagrama():
    if SIMBOLO == "anel":
        return diagrama_anel()
    m = 6.0
    L = [f'<svg class="construcao" xmlns="http://www.w3.org/2000/svg" viewBox="{vb((X0-m-3, Y0-m, LARG+2*m+12, ALT+2*m))}" role="img" aria-labelledby="ct cd">',
         '<title id="ct">Construção do símbolo TETO</title>',
         '<desc id="cd">Meio anel de raio externo φ⁵ e interno φ⁴. No topo, a barra de um T de altura φ³, tangente aos dois círculos, de x = 0 a 2r. Pilar de largura φ³ e comprimento φ⁴ centrado em x = r. Losango no mesmo eixo, centrado em (r, r), semidiagonal φ³ mais φ⁻², a √5 do pilar e do arco.</desc>',
         f'<path class="c-viga" d="{uniao_d()}"/><path class="c-anel" d="{arco_d()}"/><path class="c-los" d="{losango_d()}"/>']
    grade_base(L)
    if SIMBOLO == "t":
        L.append(f'<path class="g g-eixo" d="M{n(r)} {n(-R-3)}V{n(r+A+2)}"/>')
    L.append(f'<circle class="g g-fina" cx="{n(C[0])}" cy="{n(C[1])}" r="{n(A)}"/>')
    for y in (-R, -r):
        L.append(f'<circle class="tang" cx="0" cy="{n(y)}" r="{n(0.55)}"/>')
    yq = -R - 2.4
    _cota(L, -R, yq, 0, yq, "R = φ⁵", -R / 2, yq - 0.8)
    xq = XV + 2.4
    _cota(L, xq, -R, xq, -r, "φ³", xq + 0.8, (-R - r) / 2 + 0.6, "start")
    if SIMBOLO == "t":
        _cota(L, 0, yq, r, yq, "r", r / 2, yq - 0.8)
        _cota(L, r, yq, XV, yq, "r", (r + XV) / 2, yq - 0.8)
        _cota(L, PX0, 1.9, PX1, 1.9, "φ³", r, 4.1)
        _cota(L, xq, -r, xq, PY1, "φ⁴", xq + 0.8, -r / 2 + 0.6, "start")
        _cota(L, xq, PY1, xq, r - A, "√5", xq + 0.8, (r - A) / 2 + 0.6, "start")
        _cota(L, xq, r - A, xq, r + A, "2a", xq + 0.8, r + 0.6, "start")
    else:
        _cota(L, 0, yq, XV, yq, "R + φ⁻²", XV / 2, yq - 0.8)
        _cota(L, xq, r - A, xq, r, "a", xq + 0.8, r - A / 2 + 0.6, "start")
        _cota(L, xq, r, xq, r + A, "a = φ³ + φ⁻²", xq + 0.8, r + A / 2 + 0.6, "start")
    xl = -R - 2.4
    _cota(L, xl, 0, xl, r, "r = φ⁴", xl - 0.8, r / 2 + 0.6, "end")
    L.append("</svg>")
    return "".join(L)


def diagrama_anel():
    m = 6.0
    L = [f'<svg class="construcao" xmlns="http://www.w3.org/2000/svg" viewBox="{vb((X0-m, Y0-m, LARG+2*m+9, ALT+2*m))}" role="img" aria-labelledby="ct cd">',
         '<title id="ct">Construção do símbolo TETO</title>',
         '<desc id="cd">Anel de raio externo φ⁵ e interno φ⁴, cortado nos eixos. Losango centrado no canto do quadrado que circunscreve o vazio, com semidiagonal φ³ mais φ⁻² de compensação ótica.</desc>',
         f'<path class="c-anel" d="{arco_d()}"/><path class="c-los" d="{losango_d()}"/>']
    grade_base(L)
    L.append(f'<circle class="g g-fina" cx="{n(C[0])}" cy="{n(C[1])}" r="{n(A)}"/>')
    yq = -R - 2.4
    _cota(L, -R, yq, 0, yq, "R = φ⁵", -R / 2, yq - 0.8)
    _cota(L, 0, yq, r, yq, "r = φ⁴", r / 2, yq - 0.8)
    _cota(L, r, yq, R, yq, "φ³", (r + R) / 2, yq - 0.8)
    xq = C[0] + A + 2.4
    _cota(L, xq, 0, xq, r - A, "√5", xq + 0.8, (r - A) / 2 + 0.6, "start")
    _cota(L, xq, r - A, xq, r, "a", xq + 0.8, r - A / 2 + 0.6, "start")
    _cota(L, xq, r, xq, r + A, "a = φ³ + φ⁻²", xq + 0.8, r + A / 2 + 0.6, "start")
    L.append("</svg>")
    return "".join(L)


def diagrama_opcao(chave):
    g = geometria_opcoes()[chave]
    m = 2.5
    L = [f'<svg class="construcao evo" xmlns="http://www.w3.org/2000/svg" viewBox="{vb((X0-m, Y0-m, LARG+2*m, ALT+2*m))}" aria-hidden="true">']
    d = ""
    for p in getattr(g, "geoms", [g]):
        d += "M" + "L".join(f"{n(x)} {n(y)}" for x, y in p.exterior.coords) + "Z"
        for h in p.interiors:
            d += "M" + "L".join(f"{n(x)} {n(y)}" for x, y in h.coords) + "Z"
    L.append(f'<path class="pb" fill-rule="evenodd" d="{d}"/>')
    grade_base(L, eixo_diag=False)
    if chave == "copa":
        L.append(f'<circle class="g g-forte" cx="0" cy="0" r="{n(f(3))}"/><circle class="g g-forte" cx="0" cy="0" r="{n(f(2))}"/>')
    if chave == "empena":
        L.append(f'<path class="g g-eixo" d="M{n(-R)} {n(r)}H{n(R+2)}"/>')
    if chave in ("viga", "prumo", "junta", "pilar"):
        for y in (-R, -r):
            L.append(f'<circle class="tang" cx="0" cy="{n(y)}" r="{n(0.55)}"/>')
    if chave in ("prumo", "junta", "pilar"):
        L.append(f'<path class="g g-eixo" d="M{n(r)} {n(-R-2)}V{n(r+A+1)}"/>')
    L.append("</svg>")
    return "".join(L)


EVO = {
    "empena": ("Empena", "O anel de três quartos fica. O losango ganha uma fenda horizontal de φ¹ e a metade de cima vira telhado.",
               False, "Reprovado. Em 16 px a fenda tem 1,1 px e as metades viram um ponto. Lê como ampulheta antes de ler como casa."),
    "viga": ("Viga", "O quarto de cima à direita do anel segue reto, tangente aos dois círculos, com a mesma altura φ³: uma viga em balanço.",
             True, "Escolhido na rodada 1. Passa em 16 px, numa cor, invertido e desfocado, e a silhueta deixa de lembrar Q e lupa."),
    "copa": ("Copa", "Um segundo anel de três quartos, de φ² a φ³, entra no vazio como copa de árvore.",
             False, "Reprovado. O anel interno fica com 1,1 px em 16 px e o conjunto lê como alvo ou sinal de rede."),
    "prumo": ("a) Prumo", "O pilar desce até entrar no losango, que vira o peso de um fio de prumo pendurado na viga.",
              False, "Reprovado. Em 16 px pilar e losango viram uma seta para baixo, e a peça preta deixa de ler como T."),
    "junta": ("b) Junta", "O pilar para a E/φ³ = 1 u da ponta do losango: T e losango separados por uma junta fina, no mesmo eixo.",
              False, "Reprovado. A junta tem 0,6 px em 16 px e fecha; em tamanho pequeno vira a mesma seta do prumo."),
    "pilar": ("c) Pilar áureo", "O pilar tem largura φ³ e comprimento φ⁴ e para no eixo horizontal; o T inteiro mede φ⁵, o raio do arco. O losango fica solto a √5.",
              True, "Escolhido. O T lê de relance, não vira cruz nem seta em 16 px, e o vão de √5 passa a ser o único vão do símbolo."),
}


def bloco_evolucao(rodada):
    chaves = ("empena", "viga", "copa") if rodada == 1 else ("prumo", "junta", "pilar")
    out = ['<div class="evolucao">']
    for k in chaves:
        t, desc, ok, res = EVO[k]
        cls = " evo--escolhida" if ok else ""
        out.append(f'<figure class="evo-op{cls}"><div class="evo-op__img">{diagrama_opcao(k)}</div>'
                   f'<div class="evo-op__px"><img class="px" src="img/evolucao/{k}-16.png" width="16" height="16" alt="{t} em 16 px" loading="lazy" />'
                   f'<img class="px" src="img/evolucao/{k}-32.png" width="32" height="32" alt="{t} em 32 px" loading="lazy" /></div>'
                   f'<figcaption><b>{t}.</b> {desc} <span class="{"res res--ok" if ok else "res res--x"}">{res}</span></figcaption></figure>')
    out.append("</div>")
    return "".join(out)


def sprite():
    txt, caixa_h, _ = assinatura_horizontal()
    (sdx, sdy), txtv, caixa_v = assinatura_vertical()
    extra = ""
    if SIMBOLO != "anel":
        extra = f'<path id="p-uniao" d="{uniao_d()}"/><path id="p-vuniao" d="{uniao_d(sdx, sdy)}"/>'
    return ('<svg class="sprite" aria-hidden="true" focusable="false"><defs>'
            f'<path id="p-anel" d="{arco_d()}"/><path id="p-los" d="{losango_d()}"/>'
            f'<path id="p-hlet" d="{" ".join(txt)}"/>'
            f'<path id="p-vanel" d="{arco_d(sdx, sdy)}"/><path id="p-vlos" d="{losango_d(sdx, sdy)}"/>'
            f'<path id="p-vlet" d="{" ".join(txtv)}"/>' + extra +
            "</defs></svg>"), vb((X0, Y0, LARG, ALT)), vb(caixa_h), vb(caixa_v)


def _uses():
    base = '<use href="#p-anel" class="c-anel"/><use href="#p-los" class="c-los"/><use href="#p-hlet" class="c-let"/>'
    if SIMBOLO != "anel":
        base = '<use href="#p-uniao" class="c-viga"/>' + base
    return base


def diagrama_assinatura():
    txt, (cx, cy, cw, ch), m = assinatura_horizontal()
    pt, pb, pl = 6.5, 7.5, 6.0
    L = [f'<svg class="construcao" xmlns="http://www.w3.org/2000/svg" viewBox="{vb((cx - pl, cy - pt, cw + pl + 4, ch + pt + pb))}" role="img" aria-labelledby="at">',
         '<title id="at">Medidas da assinatura horizontal</title>',
         _uses()]
    a = L.append
    h = R / 2
    xa, xb = cx - pl, cx + cw + 2
    a(f'<path class="g g-fina" d="M{n(xa)} {n(-h)}H{n(xb)}M{n(xa)} {n(h)}H{n(xb)}M{n(m["x_desc"]-1)} {n(-h+f(3))}H{n(xb)}M{n(m["x_desc"]-1)} {n(h-f(3))}H{n(xb)}"/>')
    a(f'<path class="g g-fina" d="M{n(m["x_teto"]-f(4))} {n(cy-pt)}V{n(cy+ch+pb)}M{n(m["x_teto"])} {n(cy-pt)}V{n(cy+ch+pb)}'
      f'M{n(m["x_fio"])} {n(cy-pt)}V{n(cy+ch+pb)}M{n(m["x_desc"])} {n(cy-pt)}V{n(cy+ch+pb)}"/>')

    def cota_h(x1, x2, y, t):
        a(f'<path class="cota" d="M{n(x1)} {n(y)}H{n(x2)}M{n(x1)} {n(y-0.8)}v{n(1.6)}M{n(x2)} {n(y-0.8)}v{n(1.6)}"/>')
        a(f'<text class="rot" x="{n((x1+x2)/2)}" y="{n(y-1.1)}" text-anchor="middle">{t}</text>')

    def cota_v(x, y1, y2, t, anc="end"):
        a(f'<path class="cota" d="M{n(x)} {n(y1)}V{n(y2)}M{n(x-0.8)} {n(y1)}h{n(1.6)}M{n(x-0.8)} {n(y2)}h{n(1.6)}"/>')
        a(f'<text class="rot" x="{n(x+(-1.2 if anc == "end" else 1.2))}" y="{n((y1+y2)/2+0.9)}" text-anchor="{anc}">{t}</text>')

    yb = cy + ch + 4.5
    cota_h(m["x_teto"] - f(4), m["x_teto"], yb, "φ⁴")
    cota_h(m["x_teto"] + m["w_teto"], m["x_fio"], yb, "φ³")
    cota_h(m["x_fio"] + f(0), m["x_desc"], yb, "φ³")
    cota_v(cx - 2.2, -h, h, "φ⁵")
    xd = m["x_desc"] + m["w_desc"] + 1.6
    cota_v(xd, -h, -h + f(3), "φ³", "start")
    cota_v(xd, -h + f(3), h - f(3), "φ²", "start")
    cota_v(xd, h - f(3), h, "φ³", "start")
    a("</svg>")
    return "".join(L)


def diagrama_protecao():
    txt, (cx, cy, cw, ch), m = assinatura_horizontal()
    p, mg = PROTECAO, 2.0
    L = [f'<svg class="construcao" xmlns="http://www.w3.org/2000/svg" viewBox="{vb((cx - p - mg, cy - p - mg, cw + 2*(p+mg), ch + 2*(p+mg)))}" role="img" aria-labelledby="pt">',
         '<title id="pt">Área de proteção da assinatura horizontal</title>',
         f'<rect class="zona" x="{n(cx-p)}" y="{n(cy-p)}" width="{n(cw+2*p)}" height="{n(ch+2*p)}"/>',
         f'<rect class="miolo" x="{n(cx)}" y="{n(cy)}" width="{n(cw)}" height="{n(ch)}"/>',
         _uses()]
    for (x, y) in ((cx - p, cy - p), (cx + cw, cy - p), (cx - p, cy + ch), (cx + cw, cy + ch)):
        L.append(f'<rect class="modulo" x="{n(x)}" y="{n(y)}" width="{n(p)}" height="{n(p)}"/>')
    L.append(f'<text class="rot" x="{n(cx - p/2)}" y="{n(cy - p/2 + 1.0)}" text-anchor="middle">φ³</text>')
    L.append("</svg>")
    return "".join(L)


# ----------------------------------------------------------------------
# Ornamentos
# ----------------------------------------------------------------------
# Todos em u, desenhados com as formas do símbolo: arco de quarto/meio
# círculo, losango, viga (barra de altura constante) e círculos da série.
ORN = {}


def _svgo(nome, vbx, corpo, w=None, h=None, titulo=""):
    x, y, ww, hh = vbx
    dims = (f' width="{w}" height="{h}"' if w else "")
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{n(x)} {n(y)} {n(ww)} {n(hh)}"{dims}>'
         + (f"<title>{titulo}</title>" if titulo else "") + corpo + "</svg>\n")
    os.makedirs(OUT_ORN, exist_ok=True)
    open(os.path.join(OUT_ORN, nome), "w", encoding="utf-8").write(s)
    ORN[nome] = s
    return nome


def _arco_traco(cx, cy, rad, a0, a1, w):
    """Faixa de arco (anel parcial) como path preenchido: raio médio rad, espessura w, de a0 a a1 graus (y para baixo)."""
    ro, ri = rad + w / 2, rad - w / 2
    p = lambda rr, a: (cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a)))
    (x1, y1), (x2, y2) = p(ro, a0), p(ro, a1)
    (x3, y3), (x4, y4) = p(ri, a1), p(ri, a0)
    large = 1 if abs(a1 - a0) > 180 else 0
    sw = 1 if a1 > a0 else 0
    return (f"M{n(x1)} {n(y1)}A{n(ro)} {n(ro)} 0 {large} {sw} {n(x2)} {n(y2)}L{n(x3)} {n(y3)}"
            f"A{n(ri)} {n(ri)} 0 {large} {1-sw} {n(x4)} {n(y4)}Z")


def _ret(x, y, w, h):
    return f"M{n(x)} {n(y)}h{n(w)}v{n(h)}h{n(-w)}Z"


CORES_ORN = ((GRAMA, "grama"), (CAL, "cal"))

# Ornamentos aprovados (regra: premium = econômico; um ornamento por área).
#   divisor-laje : a viga verde sobre dois pilares (Casa T+J, Casa J.E.). Só em Grama; Cal sobre escuro.
#   caixilho     : retângulo áureo dividido em quadrados da série (Casa Bela Vista). Ferro a 30%.
#   linha        : uma linha vertical fina que acompanha o texto. Ferro a 30%.
OPAC = 0.3


def orn_divisor():
    """Laje em balanço (Casa T+J, Casa J.E.): viga de altura φ⁰ sobre dois pilares finos de
    largura φ⁻¹ e altura φ¹; a viga passa φ⁴ de cada pilar. Largura total φ⁷."""
    W, tv, lp, hp, bal = f(7), f(0), f(-1), f(1), f(4)
    d = _ret(0, 0, W, tv) + _ret(bal - lp / 2, tv, lp, hp) + _ret(W - bal - lp / 2, tv, lp, hp)
    return [_svgo(f"divisor-laje-{k}.svg", (0, 0, W, tv + hp), f'<path fill="{c}" d="{d}"/>', titulo="Divisor laje em balanço TETO")
            for c, k in CORES_ORN]


def orn_caixilho():
    """Caixilho (Casa Bela Vista): retângulo áureo φ⁶ × φ⁵ dividido em quadrados da série,
    como montantes e travessas de um caixilho de ferro. Traço de 1 px que não escala."""
    W, H = f(6), f(5)
    linhas = [
        (f(5), 0, f(5), H),
        (f(5), f(4), W, f(4)),
        (W - f(3), f(4), W - f(3), H),
        (f(5), H - f(2), W - f(3), H - f(2)),
        (f(5) + f(1), f(4), f(5) + f(1), H - f(2)),
        (f(5) + f(1), f(4) + f(0), W - f(3), f(4) + f(0)),
    ]
    d = "".join(f"M{n(a)} {n(b)}L{n(c)} {n(e)}" for a, b, c, e in linhas)
    out = []
    for c, k, op in ((FERRO, "ferro", OPAC), (CAL, "cal", 0.4)):
        g = (f'<g fill="none" stroke="{c}" stroke-opacity="{op}" stroke-width="1"><rect x="0" y="0" width="{n(W)}" height="{n(H)}" vector-effect="non-scaling-stroke"/>'
             f'<path d="{d}" vector-effect="non-scaling-stroke"/></g>')
        out.append(_svgo(f"caixilho-{k}.svg", (0, 0, W, H), g, titulo="Caixilho áureo TETO"))
    return out


def orn_linha():
    """Linha vertical fina que acompanha o texto: 1 px que não escala, estica na altura."""
    out = []
    for c, k, op in ((FERRO, "ferro", OPAC), (CAL, "cal", 0.4)):
        nome = f"linha-{k}.svg"
        s_ = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1" preserveAspectRatio="none">'
              f'<title>Linha TETO</title><path fill="none" stroke="{c}" stroke-opacity="{op}" stroke-width="1" vector-effect="non-scaling-stroke" d="M1 0V1"/></svg>\n')
        os.makedirs(OUT_ORN, exist_ok=True)
        open(os.path.join(OUT_ORN, nome), "w", encoding="utf-8").write(s_)
        ORN[nome] = s_
        out.append(nome)
    return out


def escrever_ornamentos():
    arquivos = []
    import glob
    for velho in glob.glob(os.path.join(OUT_ORN, "*.svg")):   # pasta só de arquivos gerados
        os.remove(velho)
    for fn in (orn_divisor, orn_caixilho, orn_linha):
        arquivos += fn()
    return arquivos


# ----------------------------------------------------------------------
# Contraste
# ----------------------------------------------------------------------
def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(h):
    r_, g_, b_ = hexrgba(h)[:3]
    return 0.2126 * _lin(r_) + 0.7152 * _lin(g_) + 0.0722 * _lin(b_)


def contraste(a, b):
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


PALETA = {"Grama": GRAMA, "Grama profundo": GRAMA_P, "Ferro": FERRO, "Pedra": PEDRA,
          "Telha": TELHA, "Broto": BROTO, "Cal": CAL, "Branco": BRANCO, "Cal escuro": CAL_E}


def tabela_contraste():
    fundos = ["Cal", "Cal escuro", "Branco", "Grama", "Grama profundo", "Ferro"]
    textos = ["Grama", "Grama profundo", "Ferro", "Pedra", "Telha", "Broto", "Cal", "Branco"]
    o = ['<table class="contraste"><caption>Razão de contraste WCAG 2.x, calculada pela luminância relativa '
         '(gerada por construcao/gerar_marca.py). AA exige 4,5:1 para texto e 3:1 para texto grande '
         '(24 px, ou 18,7 px em negrito) e para elementos gráficos.</caption>',
         '<thead><tr><th scope="col">Texto sobre</th>' + "".join(f'<th scope="col">{x}</th>' for x in fundos) + "</tr></thead><tbody>"]
    for t in textos:
        row = f'<tr><th scope="row">{t}</th>'
        for fu in fundos:
            if t == fu:
                row += '<td class="na">—</td>'
                continue
            v = contraste(PALETA[t], PALETA[fu])
            s = ("%.2f" % v).replace(".", ",")
            cls, lab = ("aa", "AA") if v >= 4.5 else (("ag", "grande") if v >= 3 else ("x", "falha"))
            row += (f'<td class="{cls}" style="--f:{PALETA[fu]};--t:{PALETA[t]}">'
                    f'{s} <small>{lab}</small></td>')
        o.append(row + "</tr>")
    o.append("</tbody></table>")
    return "".join(o)


def data_uri(svg_txt):
    from urllib.parse import quote
    t = re.sub(r"<title>.*?</title>", "", svg_txt).strip().replace('"', "'")
    return "data:image/svg+xml," + quote(t, safe=" /:=';,.-()")


TOKENS_ORN = [
    ("divisor-laje-grama", "divisor-laje-grama.svg"),
    ("divisor-laje-cal", "divisor-laje-cal.svg"),
    ("caixilho-ferro", "caixilho-ferro.svg"),
    ("caixilho-cal", "caixilho-cal.svg"),
    ("linha-ferro", "linha-ferro.svg"),
    ("linha-cal", "linha-cal.svg"),
]


def tokens_ornamentos():
    linhas = ["\n:root {",
              "  /* Ornamentos (gerados por construcao/gerar_marca.py; arquivos em brand/ornamentos/).",
              "     Data URI: funciona de qualquer pasta. Proporções (largura/altura) ao lado. */"]
    for k, arq in TOKENS_ORN:
        vbx = re.search(r'viewBox="([^"]+)"', ORN[arq]).group(1).split()
        razao = float(vbx[2]) / float(vbx[3])
        linhas.append(f'  --teto-orn-{k}: url("{data_uri(ORN[arq])}"); /* {razao:.3f} */')
    linhas += ["  --teto-orn-divisor-altura: 16px;     /* mínimo 10 px: pilar de 2,4 px */",
               "  --teto-orn-caixilho-traco: 1px;      /* Ferro a 30%; o traço não escala; grade com 320 px ou mais */",
               "  --teto-orn-linha-traco: 1px;         /* Ferro a 30%; uma só linha por página */",
               "}\n"]
    return "\n".join(linhas)


def injetar_css(css_path, marcador, conteudo):
    s = open(css_path, encoding="utf-8").read()
    pat = re.compile(r"(/\* gerar:%s \*/).*?(/\* /gerar:%s \*/)" % (marcador, marcador), re.S)
    if pat.search(s):
        s = pat.sub(lambda m: m.group(1) + conteudo + m.group(2), s)
    else:
        s = s.rstrip() + "\n\n/* gerar:%s */%s/* /gerar:%s */\n" % (marcador, conteudo, marcador)
    open(css_path, "w", encoding="utf-8", newline="\n").write(s)


def injetar(html_path, marcador, conteudo):
    if not os.path.exists(html_path):
        return False
    s = open(html_path, encoding="utf-8").read()
    pat = re.compile(r"(<!-- gerar:%s -->).*?(<!-- /gerar:%s -->)" % (marcador, marcador), re.S)
    if not pat.search(s):
        return False
    s = pat.sub(lambda m: m.group(1) + conteudo + m.group(2), s)
    open(html_path, "w", encoding="utf-8", newline="\n").write(s)
    return True


# ----------------------------------------------------------------------
def _eixos(txt):
    out = {}
    for parte in filter(None, (p.strip() for p in txt.split(","))):
        k, v = parte.split("=")
        out[k.strip()] = float(v)
    return out


def argumentos():
    global FONTE_LETREIRO, EIXOS_LETREIRO, TRACK_LETREIRO, FONTE_DESCRITOR, EIXOS_DESCRITOR, TRACK_DESCRITOR
    ap = argparse.ArgumentParser(description="Gera a marca TETO.")
    ap.add_argument("--fonte-letreiro")
    ap.add_argument("--eixos-letreiro", help='ex.: "wdth=75,wght=800"; vazio para fonte estática')
    ap.add_argument("--track-letreiro", type=float)
    ap.add_argument("--fonte-descritor")
    ap.add_argument("--eixos-descritor")
    ap.add_argument("--track-descritor", type=float)
    ap.add_argument("--simbolo", choices=("anel", "viga", "t"), help="variante do símbolo (padrão: anel, a aprovada)")
    a = ap.parse_args()
    if a.simbolo:
        _definir_variante(a.simbolo)
    abs_ = lambda p: p if os.path.isabs(p) else os.path.join(BRAND, p)
    if a.fonte_letreiro:
        FONTE_LETREIRO = abs_(a.fonte_letreiro)
        if not a.fonte_descritor:
            FONTE_DESCRITOR = FONTE_LETREIRO
    if a.eixos_letreiro is not None:
        EIXOS_LETREIRO = _eixos(a.eixos_letreiro)
    if a.track_letreiro is not None:
        TRACK_LETREIRO = a.track_letreiro
    if a.fonte_descritor:
        FONTE_DESCRITOR = abs_(a.fonte_descritor)
    if a.eixos_descritor is not None:
        EIXOS_DESCRITOR = _eixos(a.eixos_descritor)
    if a.track_descritor is not None:
        TRACK_DESCRITOR = a.track_descritor


def main():
    argumentos()
    ok, linhas = verificar()
    gerados, med = escrever_logos()
    escrever_pngs()
    escrever_testes()
    orn = escrever_ornamentos()
    injetar_css(os.path.join(BRAND, "tokens.css"), "ornamentos", tokens_ornamentos())
    html = os.path.join(BRAND, "index.html")
    sp, vb_s, vb_h, vb_v = sprite()
    # viewBox das marcas no manual (atributo data-vb) e proporções em tokens.css
    if os.path.exists(html):
        h = open(html, encoding="utf-8").read()
        for k, v in (("s", vb_s), ("h", vb_h), ("v", vb_v)):
            h = re.sub(r'data-vb="%s" viewBox="[^"]*"' % k, 'data-vb="%s" viewBox="%s"' % (k, v), h)
        open(html, "w", encoding="utf-8", newline="\n").write(h)
    raz = lambda v: float(v.split()[2]) / float(v.split()[3])
    injetar_css(os.path.join(BRAND, "tokens.css"), "proporcoes",
                "\n:root {\n  /* Proporções das assinaturas (largura / altura), geradas pelo script */\n"
                f"  --teto-razao-simbolo: {raz(vb_s):.4f};\n  --teto-razao-horizontal: {raz(vb_h):.4f};\n"
                f"  --teto-razao-vertical: {raz(vb_v):.4f};\n}}\n")
    for marc, cont in (("sprite", sp), ("construcao", diagrama()), ("assinatura", diagrama_assinatura()),
                       ("protecao", diagrama_protecao()), ("contraste", tabela_contraste())):
        injetar(html, marc, cont)
    linhas += ["", f"Letreiro: {os.path.relpath(FONTE_LETREIRO, BRAND)} {EIXOS_LETREIRO} track {TRACK_LETREIRO}",
               f"Descritor: {os.path.relpath(FONTE_DESCRITOR, BRAND)} {EIXOS_DESCRITOR} track {TRACK_DESCRITOR}",
               "", "Contraste (WCAG 2.x):"]
    for t, fu in (("Grama", "Cal"), ("Grama", "Branco"), ("Grama", "Ferro"), ("Grama", "Cal escuro"),
                  ("Grama profundo", "Cal"), ("Ferro", "Cal"), ("Ferro", "Grama profundo"), ("Telha", "Cal"),
                  ("Broto", "Ferro"), ("Broto", "Cal"), ("Branco", "Grama"), ("Pedra", "Cal")):
        linhas.append(f"  {t} / {fu}: {contraste(PALETA[t], PALETA[fu]):.2f}:1")
    linhas += ["", f"viewBox símbolo: {vb_s}", f"viewBox horizontal: {vb_h}", f"viewBox vertical: {vb_v}",
               "Assinatura horizontal (u): " + ", ".join(f"{k} {v:.3f}" for k, v in med.items()),
               "Logo: " + ", ".join(gerados), "Ornamentos: " + ", ".join(orn)]
    rel = "\n".join(linhas) + "\n"
    open(os.path.join(BRAND, "construcao", "verificacao.txt"), "w", encoding="utf-8").write(rel)
    sys.stdout.buffer.write(rel.encode("utf-8"))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
