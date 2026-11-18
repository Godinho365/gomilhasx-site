#!/usr/bin/env python3
"""Gera versões menores das imagens do site (para srcset) e a fonte da marca reduzida. Precisa de Pillow, fontTools e brotli:

    /home/deploy/balcao_gomilhasx-app/.venv/bin/python ferramentas/otimizar_imagens.py

Rode de novo só quando trocar ou acrescentar uma foto/tela; a saída vai para o git (o servidor não roda isto).
Saída:
  assets/r/<pasta>-<nome>-<largura>.webp   versões de 480, 720, 960 e 1440 px (fotos) ou 300 e 450 px (telas de celular),
                                           só as menores que o original; o original continua sendo a maior opção do srcset
  assets/r/fundador-96.webp                avatar quadrado do fundador (40–44 px na tela)
  assets/r/<programa>-96.webp              logos dos programas (26 a 40 px na tela; o PNG de 128 px continua para quem usa)
  assets/imagens.json                      largura e altura de cada original e das versões; o gerar_site.py lê para
                                           montar srcset e sizes (só biblioteca padrão)
  assets/inter-marca.woff2                 Inter só com as letras da marca e os símbolos que caem nela (era 52 KB)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "assets/r"
QUALIDADE = 74
GRUPOS = {"fotos": (480, 720, 960, 1440), "telas": (300, 450)}
PROGRAMAS = ["smiles", "latam-pass", "azul-fidelidade", "livelo", "esfera", "tap-miles-go", "flying-blue", "iberia",
             "connectmiles", "all-accor"]


def salvar(im: Image.Image, destino: Path) -> None:
    im.save(destino, "WEBP", quality=QUALIDADE, method=6)


def principal() -> None:
    SAIDA.mkdir(exist_ok=True)
    manifesto: dict[str, dict] = {}
    for pasta, larguras in GRUPOS.items():
        for f in sorted((RAIZ / "assets" / pasta).glob("*.webp")):
            im = Image.open(f)
            im.load()
            w, h = im.size
            versoes = []
            for lw in larguras:
                if lw >= w * 0.9:  # quase do tamanho do original: não compensa
                    continue
                lh = round(h * lw / w)
                destino = SAIDA / f"{pasta}-{f.stem}-{lw}.webp"
                salvar(im.resize((lw, lh), Image.LANCZOS), destino)
                versoes.append(["/" + str(destino.relative_to(RAIZ)), lw])
            manifesto["/" + str(f.relative_to(RAIZ))] = {"w": w, "h": h, "versoes": versoes}

    # avatar do fundador: recorte central quadrado (o mesmo que object-fit: cover mostra) em 96 px
    im = Image.open(RAIZ / "assets/fundador.webp")
    w, h = im.size
    lado = min(w, h)
    topo = (h - lado) // 2
    salvar(im.crop((0, topo, lado, topo + lado)).resize((96, 96), Image.LANCZOS), SAIDA / "fundador-96.webp")

    for nome in PROGRAMAS:
        im = Image.open(RAIZ / f"assets/{nome}.png").convert("RGBA")
        salvar(im.resize((96, 96), Image.LANCZOS), SAIDA / f"{nome}-96.webp")

    (RAIZ / "assets/imagens.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    fonte_marca()
    for p in sorted(SAIDA.iterdir()):
        print(f"{p.relative_to(RAIZ)}  {p.stat().st_size // 1024} KB")


def fonte_marca() -> None:
    """Inter aparece só no nome da marca (.wm) e como reserva da Stack Sans Headline para símbolos que ela não tem.
    Reduz o arquivo a essas letras, mantendo o eixo de peso (o CSS usa 700 a 900)."""
    from fontTools import subset
    from fontTools.ttLib import TTFont

    stack = set()
    for arq in ("stack-sans-headline-latin.woff2", "stack-sans-headline-latin-ext.woff2"):
        stack |= set(TTFont(RAIZ / "assets" / arq).getBestCmap())
    texto = ""
    for f in list((RAIZ / "_fontes").rglob("*.html")) + [RAIZ / "assets/lead.js", RAIZ / "assets/site.css"]:
        texto += re.sub(r"<[^>]+>", " ", f.read_text(encoding="utf-8"))
    sobra = {c for c in texto if ord(c) > 0x7F and ord(c) not in stack and c.isprintable()}
    letras = "GONORTEMilhasX" + "".join(sorted(sobra))
    opcoes = subset.Options()
    opcoes.flavor = "woff2"
    opcoes.layout_features = ["kern", "liga", "calt"]
    opcoes.name_IDs = ["*"]
    fonte = TTFont(RAIZ / "assets/inter.woff2")
    sub = subset.Subsetter(opcoes)
    sub.populate(text=letras)
    sub.subset(fonte)
    fonte.flavor = "woff2"
    fonte.save(RAIZ / "assets/inter-marca.woff2")
    print("inter-marca.woff2:", " ".join(f"U+{ord(c):04X}" for c in letras), f"{(RAIZ / 'assets/inter-marca.woff2').stat().st_size // 1024} KB")


if __name__ == "__main__":
    principal()
