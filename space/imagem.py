# -*- coding: utf-8 -*-
"""
Espelho da Alma — gerador do pôster compartilhável da reflexão do Diário.

Transforma a reflexão da IA num pôster vertical (1080x1350, formato Instagram)
com o clima místico do app: fundo escuro, brilho roxo, estrelas, detalhes em
dourado. A pessoa baixa e posta. Fontes funcionam no Windows e no Linux (Space).
"""

import random

from PIL import Image, ImageDraw, ImageFont

# --- dimensões e paleta (mesma do app) -------------------------------------
W, H = 1080, 1350
FUNDO_BAIXO = (7, 4, 15)       # #07040f
FUNDO_CIMA = (26, 16, 56)      # roxo
DOURADO = (201, 168, 76)       # #c9a84c
TEXTO = (236, 232, 245)        # #ece8f5
DIM = (155, 138, 184)          # #9b8ab8

# fontes serifadas: tenta Windows (local) e depois Linux (HF Space)
_CANDIDATOS = {
    "regular": [
        "C:/Windows/Fonts/georgia.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    ],
    "bold": [
        "C:/Windows/Fonts/georgiab.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ],
    "italic": [
        "C:/Windows/Fonts/georgiai.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    ],
}


def _fonte(estilo, tam):
    for caminho in _CANDIDATOS.get(estilo, []) + _CANDIDATOS["regular"]:
        try:
            return ImageFont.truetype(caminho, tam)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=tam)
    except Exception:
        return ImageFont.load_default()


def _fundo():
    """Gradiente escuro + brilho roxo no topo + estrelas + pontinhos dourados."""
    img = Image.new("RGB", (W, H), FUNDO_BAIXO)
    px = img.load()
    for y in range(H):
        t = max(0.0, 1 - (y / (H * 0.62)))  # mais claro em cima
        r = int(FUNDO_BAIXO[0] + (FUNDO_CIMA[0] - FUNDO_BAIXO[0]) * t)
        g = int(FUNDO_BAIXO[1] + (FUNDO_CIMA[1] - FUNDO_BAIXO[1]) * t)
        b = int(FUNDO_BAIXO[2] + (FUNDO_CIMA[2] - FUNDO_BAIXO[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)

    # brilho radial roxo atrás do topo
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = int(W * 0.5), int(H * 0.16)
    for raio in range(460, 0, -8):
        a = int(22 * (1 - raio / 460))
        gd.ellipse([cx - raio, cy - raio, cx + raio, cy + raio], fill=(150, 90, 220, a))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

    # estrelas (brancas) + alguns pontos dourados
    d = ImageDraw.Draw(img)
    rnd = random.Random(11)
    for _ in range(120):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        if rnd.random() < 0.2:
            d.ellipse([x, y, x + 2, y + 2], fill=DOURADO)
        else:
            v = rnd.randint(60, 170)
            d.ellipse([x, y, x + 1, y + 1], fill=(v, v, v + 20))
    return img


def _quebrar(draw, texto, fonte, larg_max):
    linhas, atual = [], ""
    for p in texto.split():
        teste = (atual + " " + p).strip()
        if draw.textlength(teste, font=fonte) <= larg_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def _centro(draw, texto, fonte, y, cor):
    w = draw.textlength(texto, font=fonte)
    draw.text(((W - w) / 2, y), texto, font=fonte, fill=cor)


def gerar_poster(reflexao, pergunta, idioma="pt"):
    """Desenha o pôster da reflexão e devolve um PIL.Image."""
    img = _fundo()
    d = ImageDraw.Draw(img)

    f_marca = _fonte("bold", 30)
    f_pergunta = _fonte("italic", 26)
    f_corpo = _fonte("regular", 42)
    f_assin = _fonte("italic", 22)

    # anel do espelho
    cx, cy = W // 2, 150
    for r, a in [(46, 110), (40, 200), (33, 90)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=DOURADO, width=2)

    # título
    titulo = "ESPELHO DA ALMA" if idioma == "pt" else "MIRROR OF THE SOUL"
    _centro(d, " ".join(titulo), f_marca, 225, DOURADO)

    # a pergunta do Diário (contexto, em itálico dourado-claro)
    for ln in _quebrar(d, pergunta, f_pergunta, W - 220):
        _centro(d, ln, f_pergunta, 300 + 0, (210, 188, 130))
        # (apenas 1ª linha esperada; se quebrar, empilha)
        # nota: pergunta costuma caber em 1-2 linhas
        break
    # se a pergunta tiver 2 linhas, desenha a 2ª
    linhas_p = _quebrar(d, pergunta, f_pergunta, W - 220)
    if len(linhas_p) > 1:
        _centro(d, linhas_p[1], f_pergunta, 336, (210, 188, 130))

    # a reflexão (texto principal), centralizada verticalmente no meio
    linhas = _quebrar(d, reflexao, f_corpo, W - 200)
    alt = 60
    bloco = len(linhas) * alt
    y = max(430, int(H * 0.52 - bloco / 2))
    for ln in linhas:
        _centro(d, ln, f_corpo, y, TEXTO)
        y += alt

    # assinatura
    assin = "feito por um modelo pequeno · com alma" if idioma == "pt" \
        else "made by a small model · with soul"
    _centro(d, assin, f_assin, H - 70, DIM)

    return img
