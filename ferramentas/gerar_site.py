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
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def data_iso(d: str) -> str:
    """Data do artigo (AAAA-MM-DD) no formato completo com fuso de Brasília, como o Google recomenda no BlogPosting."""
    return f"{d}T09:00:00-03:00" if len(d) == 10 else d

RAIZ = Path(__file__).resolve().parents[1]
FONTES = RAIZ / "_fontes"
SITE = "https://gonorte.com.br"
MENU = [("recursos", "/recursos/", "Recursos"), ("planos", "/planos/", "Planos"), ("sobre", "/sobre/", "Sobre"),
        ("blog", "/blog/", "Blog"), ("contato", "/contato/", "Contato")]
# Links para os produtos levam a origem (utm_*) para o Manager e o Balcão saberem de qual botão do site a pessoa veio.
PRODUTO_URL = re.compile(r"^https://(?:manager|balcao)\.(?:gomilhasx\.com|gonorte\.com\.br)(?=[/?#]|$)")
SEM_UTM = ("/privacidade", "/termos")  # páginas legais dos produtos: link informativo, sem medição
UTM_FIXO = (("utm_source", "gonorte.com.br"), ("utm_medium", "site"))
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


def url_com_utm(url: str, conteudo: str) -> str:
    """Acrescenta utm_source/utm_medium/utm_content ao endereço, sem tirar nem trocar os parâmetros que já existem."""
    partes = urlsplit(url)
    q = parse_qsl(partes.query, keep_blank_values=True)
    tem = {k for k, _ in q}
    q += [(k, v) for k, v in (*UTM_FIXO, ("utm_content", conteudo)) if k not in tem]
    return urlunsplit(partes._replace(path=partes.path or "/", query=urlencode(q)))


def com_utm(saida: str, onde: str, padrao: str = "") -> str:
    """Em cada <a> para manager./balcao.gonorte.com.br, troca o atributo data-utm="identificador" pelos parâmetros utm_* no href.
    Sem data-utm: usa o padrão da página (artigos: blog_<slug>); sem padrão, para a geração, para nenhum botão ficar sem
    origem. Links internos, de terceiros, páginas legais dos produtos e links que já trazem utm_source ficam como estão."""
    def troca(m: re.Match) -> str:
        tag = m.group(0)
        mh, md = re.search(r'\shref="([^"]*)"', tag), re.search(r'\sdata-utm="([^"]*)"', tag)
        if md:
            tag = tag.replace(md.group(0), "")
            if not re.fullmatch(r"[a-z0-9_]+", md.group(1)):
                raise SystemExit(f"{onde}: data-utm inválido (use letras minúsculas, números e _): {md.group(1)!r}")
        url = html.unescape(mh.group(1)) if mh else ""
        if not PRODUTO_URL.match(url):
            if md:
                raise SystemExit(f"{onde}: data-utm em link que não é do Manager nem do Balcão: {url or tag}")
            return tag
        q = dict(parse_qsl(urlsplit(url).query))
        if not md and (urlsplit(url).path.startswith(SEM_UTM) or "utm_source" in q):
            return tag
        conteudo = md.group(1) if md else padrao
        if not conteudo:
            raise SystemExit(f'{onde}: link para {url} sem data-utm="identificador_do_botao"')
        # Umami: o mesmo identificador vira o nome do botão no evento de clique (sem cookie, sem dado pessoal)
        evento = f' data-umami-event="clique_produto" data-umami-event-botao="{conteudo}"'
        return tag.replace(mh.group(0), f' href="{html.escape(url_com_utm(url, conteudo), quote=True)}"{evento}')
    return re.sub(r"<a\b[^>]*>", troca, saida)


def css_minimo(texto: str) -> str:
    """Tira comentários e espaços que não mudam nada (o CSS vai inteiro dentro de cada página)."""
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    texto = re.sub(r"\s+", " ", texto)
    return re.sub(r"\s*([{};,])\s*", r"\1", texto).replace(";}", "}").strip()


# Imagens com versões menores (ferramentas/otimizar_imagens.py): srcset montado aqui; "sizes" vem da fonte ou do padrão.
IMAGENS: dict[str, dict] = json.loads(ler(RAIZ / "assets/imagens.json"))
SIZES_PADRAO = {"/assets/fotos/": "100vw", "/assets/telas/": "(max-width: 767px) 280px, 360px"}


_VERSOES: dict[str, str] = {}


def com_versao(url: str) -> str:
    """/assets/... ganha ?v=<hash do arquivo>: o endereço muda quando o arquivo muda, então o Caddy pode guardar por 1 ano."""
    if not url.startswith("/assets/") or "?" in url:
        return url
    if url not in _VERSOES:
        _VERSOES[url] = versao(RAIZ / url.lstrip("/"))
    return f"{url}?v={_VERSOES[url]}"


def imagens_responsivas(saida: str) -> str:
    """Em cada <img> de /assets/: endereço com versão e, nas fotos e telas com versões menores, srcset + sizes."""
    def troca(m: re.Match) -> str:
        tag = m.group(0)
        ms = re.search(r'\ssrc="([^"]+)"', tag)
        if not ms:
            return tag
        src = ms.group(1)
        info = IMAGENS.get(src.split("?")[0])
        novo = f' src="{com_versao(src)}"'
        if info and info["versoes"] and " srcset=" not in tag:
            srcset = ", ".join(f"{com_versao(u)} {w}w" for u, w in info["versoes"]) + f", {com_versao(src)} {info['w']}w"
            novo += f' srcset="{srcset}"'
            if " sizes=" not in tag:
                padrao = next(v for k, v in SIZES_PADRAO.items() if src.startswith(k))
                tag = tag.replace("<img ", f'<img sizes="{padrao}" ', 1)
        return tag.replace(ms.group(0), novo, 1)
    return re.sub(r"<img\b[^>]*>", troca, saida)


def dimensoes(src: str) -> str:
    """width/height do original: o navegador reserva o espaço antes da imagem chegar (sem deslocar o layout)."""
    info = IMAGENS.get(src.split("?")[0])
    return f' width="{info["w"]}" height="{info["h"]}"' if info else ""


def preload_imagens(lista: str, conteudo: str) -> str:
    """<link rel=preload> da imagem do LCP com o mesmo srcset/sizes do <img> (senão o navegador baixa duas versões)."""
    links = []
    for src in filter(None, (x.strip() for x in lista.split(","))):
        m = re.search(r'<img\b[^>]*\ssrc="(' + re.escape(src) + r'(?:\?v=\w+)?)"[^>]*>', conteudo)
        extra = ""
        if m:
            src = m.group(1)
            for attr, nome in (("srcset", "imagesrcset"), ("sizes", "imagesizes")):
                a = re.search(rf'\s{attr}="([^"]*)"', m.group(0))
                if a:
                    extra += f' {nome}="{a.group(1)}"'
        links.append(f'<link rel="preload" as="image" href="{src}"{extra} fetchpriority="high">\n')
    return "".join(links)


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
    "css": re.sub(r'url\("(/assets/[^"?]+)"\)', lambda m: f'url("{com_versao(m.group(1))}")',
                  css_minimo(ler(RAIZ / "assets/site.css") + ler(RAIZ / "assets/motion/gomilhasx-motion.css"))),
    "fonte_titulo": com_versao("/assets/stack-sans-headline-latin.woff2"),
    "icone": com_versao("/assets/marca/icone.svg"),
    # fonte do nome no logo (3 KB): pré-carregada para não esperar o CSS pedir (cadeia de rede do PageSpeed)
    "fonte_marca": com_versao("/assets/inter-marca.woff2"),
    "motion_js": com_versao("/assets/motion/gomilhasx-motion.js"),
    "v_js": versao(RAIZ / "assets/site-motion.js"),
    "v_lead_css": versao(RAIZ / "assets/lead.css"),
    "v_lead_js": versao(RAIZ / "assets/lead.js"),
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


def montar(meta: dict[str, str], conteudo: str, extra_jsonld: list[dict] | None = None, utm_padrao: str = "") -> str:
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
    indexavel = "noindex" not in meta.get("robots", "")
    if indexavel and caminho != "/" and not any(isinstance(x, dict) and x.get("@type") == "BreadcrumbList" for x in ld):
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": meta.get("migalha", meta["titulo"].split(" | ")[0]), "item": SITE + caminho}]})
    conteudo = imagens_responsivas(conteudo)
    imagem = meta.get("imagem", "/og-image.png?v=4")
    valores = {
        **COMUM,
        "titulo": html.escape(meta["titulo"], quote=True),
        "descricao": html.escape(meta["descricao"], quote=True),
        "caminho": caminho,
        "robots": meta.get("robots", "index, follow, max-image-preview:large"),
        # página de erro (404.html) é servida em qualquer endereço: sem canonical
        "canonical": f'<link rel="canonical" href="{SITE}{caminho}">\n' if indexavel else "",
        "og_tipo": meta.get("og_tipo", "website"),
        "imagem": imagem if imagem.startswith("http") else SITE + imagem,
        "preload": preload_imagens(meta.get("preload", ""), conteudo),
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
    return com_utm(saida, caminho, utm_padrao)


def gravar(caminho: str, conteudo: str, gerados: list[str]) -> None:
    # "/404.html" (endereço terminado em .html) vira o próprio arquivo; os demais, <caminho>/index.html
    destino = RAIZ / ("index.html" if caminho == "/" else caminho.strip("/") if caminho.endswith(".html") else caminho.strip("/") + "/index.html")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding="utf-8")
    gerados.append(str(destino.relative_to(RAIZ)))


# "Leia também" no fim de cada artigo: metadado "leia:" com páginas do site (por público, ferramentas) e/ou produtos
LEIA = {
    "/para-viajantes/": ("Para viajantes", "Organize os pontos da família e compre milhas com o pagamento intermediado."),
    "/para-milheiros/": ("Para milheiros", "Custo do milheiro, lucro por venda e o Módulo Milheiro do GO Balcão."),
    "/para-agencias/": ("Para agências", "Contas de clientes, equipe e emissões com fornecedores, num lugar só."),
    "/calculadora-custo-do-milheiro/": ("Calculadora do custo do milheiro", "Grátis e sem cadastro: o custo de uma compra ou transferência."),
    "/planilha-de-milhas/": ("Planilha de milhas grátis", "Saldos, custo médio e vendas por programa, para baixar."),
    "/seguranca/": ("Segurança no GO Balcão", "Verificação de identidade, intermediação e reputação pública."),
    "/gestao-de-milhas/": ("Gestão de milhas", "O guia completo: custo, vencimentos, lucro e ferramentas grátis."),
    "/controle-de-milhas/": ("Controle de milhas", "Saldo, validade e custo de cada conta, por titular e programa."),
    "/calculadora-valor-da-milha/": ("Calculadora de valor da milha", "Quanto cada milheiro rende numa passagem, comparado ao custo."),
    "/vender-milhas/": ("Vender milhas", "Regras dos programas, riscos e como vender com segurança."),
    "/comprar-milhas/": ("Comprar milhas", "Como a compra funciona e o que conferir antes de pagar."),
    "/golpes-de-milhas/": ("Golpes com milhas", "Os golpes mais comuns e como se proteger."),
    "manager": ("https://manager.gonorte.com.br/register", "GO Manager, grátis para começar", "O custo do milheiro recalculado a cada compra, transferência e venda."),
    "balcao": ("https://balcao.gonorte.com.br/", "GO Balcão", "Compre e venda milhas com quem tem identidade conferida e PIX intermediado."),
}


def leia_tambem(slug: str, itens: str) -> str:
    lis = []
    for chave in filter(None, (x.strip() for x in itens.split(","))):
        if chave not in LEIA:
            raise SystemExit(f"blog/{slug}: leia desconhecido: {chave}")
        if chave.startswith("/"):
            nome, txt = LEIA[chave]
            lis.append(f'<li><a href="{chave}"><b>{html.escape(nome)}</b><span>{html.escape(txt)}</span></a></li>')
        else:
            url, nome, txt = LEIA[chave]
            lis.append(f'<li class="produto"><a href="{url}" data-utm="blog_{slug.replace("-", "_")}_leia_{chave}"><b>{html.escape(nome)}</b><span>{html.escape(txt)}</span></a></li>')
    if not lis:
        return ""
    return f'\n  <aside class="leia-tambem" aria-labelledby="leia-titulo"><p class="t" id="leia-titulo">Leia também</p><ul>{"".join(lis)}</ul></aside>'


def cartao_post(p: dict, destaque: bool = False) -> str:
    classe = "post-card destaque" if destaque else "post-card"
    sizes = "(max-width: 767px) 100vw, " + ("610px" if destaque else "360px")
    return (f'<a class="{classe} gx-card gx-reveal" href="/blog/{p["slug"]}/">'
            f'<span class="pc-img"><img sizes="{sizes}" src="{p["imagem"]}" alt=""{dimensoes(p["imagem"])} loading="lazy" decoding="async"></span>'
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
        if "noindex" not in meta.get("robots", ""):
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
        lista = {"@context": "https://schema.org", "@type": "Blog", "name": "Blog da GONORTE", "url": SITE + "/blog/",
                 "publisher": {"@id": SITE + "/#organization"},
                 "blogPost": [{"@type": "BlogPosting", "headline": p["titulo_curto"], "url": f"{SITE}/blog/{p['slug']}/", "datePublished": data_iso(p["data"])} for p in posts]}
        meta = {"titulo": "Blog de milhas: custo do milheiro e transferências | GONORTE", "descricao": "Guias práticos sobre milhas, custo do milheiro, transferências bonificadas e como comprar e vender milhas com segurança.",
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
    <div class="post-autor"><img src="/assets/r/fundador-96.webp" alt="" width="40" height="40"><span><b>Raphael Godinho</b><small>Sócio fundador da GONORTE</small></span></div>
  </div>
  <figure class="post-capa wrap gx-reveal"><img sizes="(max-width: 767px) 100vw, 992px" src="{p["imagem"]}" alt=""{dimensoes(p["imagem"])} fetchpriority="high"></figure>
  <div class="post-corpo wrap">
{p["corpo"].rstrip()}{leia_tambem(p["slug"], p.get("leia", ""))}
  </div>
</article>
<section class="sec off" aria-labelledby="mais-titulo">
  <div class="wrap"><h2 id="mais-titulo" class="h2" data-split>Continue lendo</h2><div class="post-grid tres">{relacionados}</div></div>
</section>
{CTA}'''
        artigo = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["titulo_curto"], "description": p["resumo"],
                  "datePublished": data_iso(p["data"]), "dateModified": data_iso(p.get("atualizado", p["data"])), "inLanguage": "pt-BR",
                  "image": SITE + p["imagem"], "mainEntityOfPage": f"{SITE}/blog/{p['slug']}/",
                  "author": {"@type": "Person", "@id": SITE + "/#fundador", "name": "Raphael Godinho", "url": SITE + "/sobre/#fundador"}, "publisher": {"@id": SITE + "/#organization"}}
        migalhas = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": p["titulo_curto"], "item": f"{SITE}/blog/{p['slug']}/"}]}
        meta = {"titulo": p["titulo"], "descricao": p["descricao"], "caminho": f"/blog/{p['slug']}/", "menu": "blog",
                "og_tipo": "article", "imagem": p["imagem"], "preload": p["imagem"], "classe": "pagina artigo"}
        gravar(meta["caminho"], montar(meta, corpo, [artigo, migalhas], utm_padrao="blog_" + p["slug"].replace("-", "_")), gerados)
        urls.append((meta["caminho"], p.get("atualizado", p["data"])))

    # Mapa do site
    # lastmod só com data informada (artigos e páginas com "atualizado:"), para a saída não mudar sozinha a cada dia
    linhas = "\n".join(f"  <url><loc>{SITE}{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>" for u, d in urls)
    (RAIZ / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{linhas}\n</urlset>\n', encoding="utf-8")
    gerados.append("sitemap.xml")
    print("\n".join(gerados))


if __name__ == "__main__":
    principal()
