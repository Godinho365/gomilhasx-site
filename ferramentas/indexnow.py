"""Avisa o Bing (e os outros buscadores do IndexNow) das páginas do sitemap.

Uso, depois de publicar: python3 ferramentas/indexnow.py [url ...]
Sem argumentos, envia todas as URLs do sitemap.xml. A chave pública fica em /b528c2642209b4e65e586ba0f00c86c7.txt na raiz do site.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
HOST = "gonorte.com.br"
CHAVE = "b528c2642209b4e65e586ba0f00c86c7"


def main() -> int:
    urls = sys.argv[1:] or re.findall(r"<loc>([^<]+)</loc>", (RAIZ / "sitemap.xml").read_text(encoding="utf-8"))
    corpo = json.dumps({"host": HOST, "key": CHAVE, "keyLocation": f"https://{HOST}/{CHAVE}.txt", "urlList": urls}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=corpo,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"IndexNow: {r.status} para {len(urls)} URL(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
