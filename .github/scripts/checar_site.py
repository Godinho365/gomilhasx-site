"""Checagem do site estático: em cada página, HTML bem fechado, JSON-LD válido e todo arquivo local referenciado existindo;
e as páginas geradas iguais às fontes (ferramentas/gerar_site.py)."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
erros: list[str] = []


class Checador(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.pilha: list[tuple[str, int]] = []
        self.refs: list[tuple[str, int]] = []
        self.jsonld: list[tuple[str, int]] = []
        self._em_jsonld = False
        self.atalho = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.atalho = self.atalho or (tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh")
        linha = self.getpos()[0]
        for k in ("src", "href", "poster"):
            if a.get(k):
                self.refs.append((a[k], linha))
        if a.get("srcset"):
            self.refs += [(p.strip().split(" ")[0], linha) for p in a["srcset"].split(",")]
        self._em_jsonld = tag == "script" and a.get("type") == "application/ld+json"
        if tag not in VOID:
            self.pilha.append((tag, linha))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.pilha.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.pilha or self.pilha[-1][0] != tag:
            aberta = self.pilha[-1] if self.pilha else ("nada", 0)
            erros.append(f"index.html:{self.getpos()[0]}: </{tag}> fecha <{aberta[0]}> da linha {aberta[1]}")
            while self.pilha and self.pilha[-1][0] != tag:
                self.pilha.pop()
        if self.pilha:
            self.pilha.pop()

    def handle_data(self, data):
        if self._em_jsonld and data.strip():
            self.jsonld.append((data, self.getpos()[0]))
            self._em_jsonld = False


paginas = sorted(p for p in ROOT.rglob("index.html") if not any(parte.startswith((".", "_")) for parte in p.relative_to(ROOT).parts))
paginas += [ROOT / "404.html"] if (ROOT / "404.html").exists() else []  # página de erro: mesma checagem, sem exigir JSON-LD
refs = []
total_jsonld = 0
for pagina in paginas:
    nome = str(pagina.relative_to(ROOT))
    c = Checador()
    c.feed(pagina.read_text(encoding="utf-8"))
    for tag, linha in c.pilha:
        erros.append(f"{nome}:{linha}: <{tag}> nunca é fechada")
    for bloco, linha in c.jsonld:
        try:
            json.loads(bloco)
        except json.JSONDecodeError as e:
            erros.append(f"{nome}:{linha}: JSON-LD inválido ({e})")
    if not c.jsonld and nome != "404.html" and not c.atalho:  # atalho (meta refresh para outro site) não leva JSON-LD
        erros.append(f"{nome}: sem JSON-LD")
    total_jsonld += len(c.jsonld)
    refs += [(r, f"{nome}:{l}") for r, l in c.refs]

# arquivos locais citados no HTML, no CSS e no JS
for f in list(ROOT.glob("assets/**/*.css")) + list(ROOT.glob("assets/**/*.js")):
    for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)", f.read_text(encoding="utf-8")):
        refs.append((str((f.parent / m.group(1)).relative_to(ROOT)) if not m.group(1).startswith("/") else m.group(1), str(f.relative_to(ROOT))))
for ref, linha in refs:
    if re.match(r"^(https?:|mailto:|tel:|data:|#|//)", ref) or ref.startswith(("/api/", "/stats/")):  # /api e /stats vêm do Caddy (Balcão e Umami)
        continue
    caminho = ref.split("#")[0].split("?")[0].lstrip("/")
    if caminho and not (ROOT / caminho).resolve().exists():
        erros.append(f"{linha}: arquivo não encontrado: {ref}")

# páginas geradas precisam estar em dia com as fontes
import subprocess
antes = {p: p.read_bytes() for p in paginas + [ROOT / "sitemap.xml", ROOT / "llms.txt", ROOT / "llms-full.txt"] if p.exists()}
subprocess.run([sys.executable, str(ROOT / "ferramentas/gerar_site.py")], check=True, capture_output=True)
for p, conteudo in antes.items():
    if p.read_bytes() != conteudo:
        erros.append(f"{p.relative_to(ROOT)}: diferente do que as fontes geram; rode python3 ferramentas/gerar_site.py e envie o resultado")
for e in erros:
    print(e)
print(f"{len(erros)} problema(s)" if erros else f"ok: {len(paginas)} páginas, {len(refs)} referências, {total_jsonld} bloco(s) JSON-LD")
sys.exit(1 if erros else 0)
