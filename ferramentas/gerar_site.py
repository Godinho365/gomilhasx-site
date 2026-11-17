#!/usr/bin/env python3
"""Gera as páginas do site institucional a partir de _fontes/ (sem dependências; só a biblioteca padrão).

    python3 ferramentas/gerar_site.py

Fontes:
  _fontes/base.html                  esqueleto comum (cabeçalho, rodapé, scripts)
  _fontes/paginas/<nome>.html        uma página; começa com um comentário de metadados (titulo, descricao, caminho...)
  _fontes/blog/<slug>.html           um artigo; metadados + corpo do texto em HTML simples (h2, p, ul, ol, blockquote)
  _fontes/icones.svg, formulario-balcao.html, whatsapp.html, jsonld-*.json
Saída (vai para o git; publicar continua sendo só "git pull"):
  index.html, <caminho>/index.html, blog/index.html, blog/<slug>/index.html, sitemap.xml
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FONTES = RAIZ / "_fontes"
SITE = "https://gomilhasx.com"
MENU = [("recursos", "/recursos/", "Recursos"), ("planos", "/planos/", "Planos"), ("sobre", "/sobre/", "Sobre"),
        ("blog", "/blog/", "Blog"), ("contato", "/contato/", "Contato")]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def ler(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def meta_e_corpo(texto: str) -> tuple[dict[str, str], str]:
    m = re.match(r"\s*<!--(.*?)-->\s*", texto, re.S)
    if not m:
        raise SystemExit("fonte sem bloco de metadados <!-- ... -->")
    meta = {}
    for linha in m.group(1).strip().splitlines():
        if ":" in linha:
            k, v = linha.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, texto[m.end():].rstrip() + "\n"


def versao(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:10]


def data_br(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def menu_html(ativo: str) -> str:
    return "".join(
        f'<a href="{href}"' + (' aria-current="page" class="on"' if chave == ativo else "") + f">{nome}</a>"
        for chave, href, nome in MENU
    )


def jsonld(itens: list[dict | str]) -> str:
    out = []
    for it in itens:
        corpo = it if isinstance(it, str) else json.dumps(it, ensure_ascii=False, separators=(",", ":"))
        out.append(f'<script type="application/ld+json">\n{corpo.strip()}\n</script>\n')
    return "".join(out)


BASE = ler(FONTES / "base.html")
COMUM = {
    "icones": ler(FONTES / "icones.svg").strip(),
    "formulario": ler(FONTES / "formulario-balcao.html").strip(),
    "whatsapp": ler(FONTES / "whatsapp.html").strip(),
    "v_css": versao(RAIZ / "assets/site.css"),
    "v_js": versao(RAIZ / "assets/site-motion.js"),
}
CTA = ler(FONTES / "cta-final.html").strip()
JSONLD_ARQ = {"organizacao": ler(FONTES / "jsonld-organizacao.json"), "faq": ler(FONTES / "jsonld-faq.json")}


def faq_da_pagina(conteudo: str) -> dict:
    """FAQPage montado com as perguntas que aparecem na própria página (<details><summary>pergunta</summary><p>resposta</p>)."""
    itens = []
    for q, a in re.findall(r"<summary>(.*?)</summary>\s*<p>(.*?)</p>", conteudo, re.S):
        texto = lambda h: html.unescape(re.sub(r"<[^>]+>", "", h)).strip()
        itens.append({"@type": "Question", "name": texto(q), "acceptedAnswer": {"@type": "Answer", "text": texto(a)}})
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": itens}


def montar(meta: dict[str, str], conteudo: str, extra_jsonld: list[dict] | None = None) -> str:
    ld: list[dict | str] = []
    for n in filter(None, (x.strip() for x in meta.get("jsonld", "").split(","))):
        if n == "faq-pagina":
            ld.append(faq_da_pagina(conteudo))
        elif n in JSONLD_ARQ:
            ld.append(JSONLD_ARQ[n])
        else:
            raise SystemExit(f"jsonld desconhecido em {meta['caminho']}: {n}")
    ld += extra_jsonld or []
    caminho = meta["caminho"]
    if caminho != "/" and not any(isinstance(x, dict) and x.get("@type") == "BreadcrumbList" for x in ld):
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": meta.get("migalha", meta["titulo"].split(" | ")[0]), "item": SITE + caminho}]})
    imagem = meta.get("imagem", "/og-image.png")
    valores = {
        **COMUM,
        "titulo": html.escape(meta["titulo"], quote=True),
        "descricao": html.escape(meta["descricao"], quote=True),
        "caminho": caminho,
        "og_tipo": meta.get("og_tipo", "website"),
        "imagem": imagem if imagem.startswith("http") else SITE + imagem,
        "preload": "".join(f'<link rel="preload" as="image" href="{p.strip()}" fetchpriority="high">\n' for p in meta.get("preload", "").split(",") if p.strip()),
        "jsonld": jsonld(ld),
        "classe": meta.get("classe", "pagina"),
        "menu": menu_html(meta.get("menu", "")),
        "conteudo": conteudo.rstrip(),
    }
    saida = BASE
    for k, v in valores.items():
        saida = saida.replace("{{" + k + "}}", v)
    resto = re.findall(r"\{\{\w+\}\}", saida)
    if resto:
        raise SystemExit(f"marcadores sem valor em {caminho}: {resto}")
    return saida


def gravar(caminho: str, conteudo: str, gerados: list[str]) -> None:
    destino = RAIZ / ("index.html" if caminho == "/" else caminho.strip("/") + "/index.html")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding="utf-8")
    gerados.append(str(destino.relative_to(RAIZ)))


def cartao_post(p: dict, destaque: bool = False) -> str:
    classe = "post-card destaque" if destaque else "post-card"
    return (f'<a class="{classe} gx-card gx-reveal" href="/blog/{p["slug"]}/">'
            f'<span class="pc-img"><img src="{p["imagem"]}" alt="" loading="lazy" decoding="async"></span>'
            f'<span class="pc-body"><span class="pc-meta"><b>{html.escape(p["categoria"])}</b> · {data_br(p["data"])} · {p["leitura"]} min de leitura</span>'
            f'<span class="pc-t">{html.escape(p["titulo_curto"])}</span><span class="pc-r">{html.escape(p["resumo"])}</span></span></a>')


def principal() -> None:
    gerados: list[str] = []
    urls: list[tuple[str, str]] = []

    # Artigos do blog
    posts = []
    for f in sorted((FONTES / "blog").glob("*.html")):
        meta, corpo = meta_e_corpo(ler(f))
        meta["slug"] = f.stem
        meta["corpo"] = corpo
        meta.setdefault("leitura", str(max(2, round(len(re.sub(r"<[^>]+>", " ", corpo).split()) / 200))))
        posts.append(meta)
    posts.sort(key=lambda p: p["data"], reverse=True)

    # Páginas
    for f in sorted((FONTES / "paginas").glob("*.html")):
        meta, corpo = meta_e_corpo(ler(f))
        corpo = corpo.replace("{{cta}}", CTA)
        if "{{blog_recentes}}" in corpo:
            corpo = corpo.replace("{{blog_recentes}}", "\n".join(cartao_post(p) for p in posts[:3]))
        gravar(meta["caminho"], montar(meta, corpo), gerados)
        urls.append((meta["caminho"], meta.get("atualizado", "")))

    # Lista do blog
    if posts:
        cats = sorted({p["categoria"] for p in posts})
        filtros = '<button type="button" aria-pressed="true" data-cat="">Todos</button>' + "".join(
            f'<button type="button" aria-pressed="false" data-cat="{html.escape(c)}">{html.escape(c)}</button>' for c in cats)
        cartoes = cartao_post(posts[0], destaque=True) + "\n" + "\n".join(
            cartao_post(p).replace('class="post-card', f'data-cat="{html.escape(p["categoria"])}" class="post-card') for p in posts[1:])
        cartoes = cartoes.replace('<a class="post-card destaque', f'<a data-cat="{html.escape(posts[0]["categoria"])}" class="post-card destaque', 1)
        corpo = f'''<section class="page-hero" aria-labelledby="titulo">
  <div class="wrap center"><span class="kicker">Blog</span><h1 id="titulo" data-split="100">Blog e artigos</h1>
  <p class="lead-p gx-reveal">Guias práticos sobre milhas, custo do milheiro, transferências e negociação com segurança.</p></div>
</section>
<section class="sec" style="padding-top:24px" aria-label="Artigos">
  <div class="wrap">
    <div class="chips-row blog-filtros" role="group" aria-label="Filtrar por assunto">{filtros}</div>
    <div class="post-grid">
{cartoes}
    </div>
  </div>
</section>
{CTA}
<script>
// Blog: filtro por assunto
(function () {{
  var bts = document.querySelectorAll(".blog-filtros button"), cards = document.querySelectorAll(".post-grid [data-cat]");
  bts.forEach(function (b) {{ b.addEventListener("click", function () {{
    var c = b.getAttribute("data-cat");
    bts.forEach(function (x) {{ x.setAttribute("aria-pressed", String(x === b)); }});
    cards.forEach(function (k) {{ k.hidden = !!c && k.getAttribute("data-cat") !== c; }});
  }}); }});
}})();
</script>'''
        lista = {"@context": "https://schema.org", "@type": "Blog", "name": "Blog da GOMilhasX", "url": SITE + "/blog/",
                 "publisher": {"@id": SITE + "/#organization"},
                 "blogPost": [{"@type": "BlogPosting", "headline": p["titulo_curto"], "url": f"{SITE}/blog/{p['slug']}/", "datePublished": p["data"]} for p in posts]}
        meta = {"titulo": "Blog de milhas: custo do milheiro e transferências | GOMilhasX", "descricao": "Guias práticos sobre milhas, custo do milheiro, transferências bonificadas e como comprar e vender milhas com segurança.",
                "caminho": "/blog/", "menu": "blog", "migalha": "Blog"}
        gravar("/blog/", montar(meta, corpo, [lista]), gerados)
        urls.append(("/blog/", posts[0]["data"]))

    # Cada artigo
    for i, p in enumerate(posts):
        outros = [q for q in posts if q is not p][:3]
        relacionados = "\n".join(cartao_post(q) for q in outros)
        corpo = f'''<article class="post">
  <div class="post-head wrap">
    <a class="post-back" href="/blog/"><svg style="transform:rotate(180deg)"><use href="#i-arrow"/></svg>Blog</a>
    <span class="pc-meta"><b>{html.escape(p["categoria"])}</b> · {data_br(p["data"])} · {p["leitura"]} min de leitura</span>
    <h1 data-split="80">{html.escape(p["titulo_curto"])}</h1>
    <p class="lead-p">{html.escape(p["resumo"])}</p>
    <div class="post-autor"><img src="/assets/fundador.webp" alt="" width="40" height="40"><span><b>Godinho</b><small>Sócio fundador da GOMilhasX</small></span></div>
  </div>
  <figure class="post-capa wrap gx-reveal"><img src="{p["imagem"]}" alt="" fetchpriority="high"></figure>
  <div class="post-corpo wrap">
{p["corpo"].rstrip()}
  </div>
</article>
<section class="sec off" aria-labelledby="mais-titulo">
  <div class="wrap"><h2 id="mais-titulo" class="h2" data-split>Continue lendo</h2><div class="post-grid tres">{relacionados}</div></div>
</section>
{CTA}'''
        artigo = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["titulo_curto"], "description": p["resumo"],
                  "datePublished": p["data"], "dateModified": p.get("atualizado", p["data"]), "inLanguage": "pt-BR",
                  "image": SITE + p["imagem"], "mainEntityOfPage": f"{SITE}/blog/{p['slug']}/",
                  "author": {"@id": SITE + "/#fundador"}, "publisher": {"@id": SITE + "/#organization"}}
        migalhas = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["titulo_curto"], "item": f"{SITE}/blog/{p['slug']}/"}]}
        meta = {"titulo": p["titulo"], "descricao": p["descricao"], "caminho": f"/blog/{p['slug']}/", "menu": "blog",
                "og_tipo": "article", "imagem": p["imagem"], "preload": p["imagem"], "classe": "pagina artigo"}
        gravar(meta["caminho"], montar(meta, corpo, [artigo, migalhas]), gerados)
        urls.append((meta["caminho"], p.get("atualizado", p["data"])))

    # Mapa do site
    # lastmod só com data informada (artigos e páginas com "atualizado:"), para a saída não mudar sozinha a cada dia
    linhas = "\n".join(f"  <url><loc>{SITE}{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>" for u, d in urls)
    (RAIZ / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{linhas}\n</urlset>\n', encoding="utf-8")
    gerados.append("sitemap.xml")
    print("\n".join(gerados))


if __name__ == "__main__":
    principal()
