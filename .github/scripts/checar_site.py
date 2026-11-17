"""Checagem do site estático: HTML bem fechado, JSON-LD válido e todo arquivo local referenciado existindo."""
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

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
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


html = (ROOT / "index.html").read_text(encoding="utf-8")
c = Checador()
c.feed(html)
for tag, linha in c.pilha:
    erros.append(f"index.html:{linha}: <{tag}> nunca é fechada")
for bloco, linha in c.jsonld:
    try:
        json.loads(bloco)
    except json.JSONDecodeError as e:
        erros.append(f"index.html:{linha}: JSON-LD inválido ({e})")
if not c.jsonld:
    erros.append("index.html: sem JSON-LD")

# arquivos locais citados no HTML, no CSS e no JS
refs = list(c.refs)
for f in list(ROOT.glob("assets/**/*.css")) + list(ROOT.glob("assets/**/*.js")):
    for m in re.finditer(r"url\(\s*['\"]?([^'\")]+)", f.read_text(encoding="utf-8")):
        refs.append((str((f.parent / m.group(1)).relative_to(ROOT)) if not m.group(1).startswith("/") else m.group(1), 0))
for ref, linha in refs:
    if re.match(r"^(https?:|mailto:|tel:|data:|#|//)", ref) or ref.startswith("/api/"):
        continue
    caminho = ref.split("#")[0].split("?")[0].lstrip("/")
    if caminho and not (ROOT / caminho).resolve().exists():
        erros.append(f"index.html:{linha}: arquivo não encontrado: {ref}")

for e in erros:
    print(e)
print(f"{len(erros)} problema(s)" if erros else f"ok: {len(refs)} referências, {len(c.jsonld)} bloco(s) JSON-LD")
sys.exit(1 if erros else 0)
