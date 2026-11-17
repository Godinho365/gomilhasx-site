# gomilhasx-site

Site institucional da GOMilhasX em https://gomilhasx.com: apresenta o GO Manager e o GO Balcão e os planos de cada um.

Site estático (HTML, CSS e imagens). As páginas são geradas por `ferramentas/gerar_site.py` a partir de `_fontes/` e o resultado vai para o git, então o servidor não precisa de build. No servidor fica em `/home/deploy/gomilhasx-app` e o Caddy do Manager
(projeto `milhasx`) monta a pasta em `/srv/institucional` e a serve direto no bloco `gomilhasx.com`.

## Publicar uma mudança

```bash
cd /home/deploy/gomilhasx-app && git pull
```

Não precisa reiniciar nada: o Caddy lê os arquivos a cada pedido (o HTML vai com `Cache-Control: no-cache`).

## Páginas e blog

Páginas: `/` (início), `/recursos/`, `/planos/`, `/sobre/`, `/contato/`, `/duvidas/`, `/blog/` e um endereço por artigo.
Não edite os `index.html` à mão: edite a fonte e gere de novo.

```bash
python3 ferramentas/gerar_site.py
```

- `_fontes/base.html`: cabeçalho, rodapé, scripts e metadados comuns.
- `_fontes/paginas/<nome>.html`: cada página, começando por um bloco `<!-- titulo: ... descricao: ... caminho: ... -->`.
  `jsonld: faq-pagina` monta o FAQ para o Google com as perguntas da própria página; `{{cta}}` coloca a chamada final.
- `_fontes/blog/<slug>.html`: cada artigo (o nome do arquivo vira o endereço `/blog/<slug>/`). Metadados: `titulo`, `titulo_curto`,
  `descricao`, `resumo`, `data` (AAAA-MM-DD), `categoria`, `imagem`. O corpo é HTML simples (`h2`, `p`, `ul`, `ol`, `table`,
  `blockquote`, `<div class="conta">` para destacar uma conta, `<p class="aviso">` para a nota final).
- O gerador também refaz `sitemap.xml`. A checagem do CI (`.github/scripts/checar_site.py`) confere todas as páginas e avisa se
  alguma página não foi gerada de novo depois de mudar a fonte.
- Estilos em `assets/site.css`; animações em `assets/site-motion.js` (as páginas usam a versão do arquivo no endereço, então a
  mudança aparece na hora).
- Novas páginas precisam ser liberadas no Caddy do Manager (`docker/Caddyfile`, bloco `gomilhasx.com`, matcher `@site`).

## Preços

A página mostra só um resumo (os planos completos ficam nos sites de cada produto). Os valores do resumo são
copiados dos apps; ao mudar um preço lá, confira a seção "Planos" de `_fontes/paginas/inicio.html` e a página `_fontes/paginas/planos.html`:

- **Manager**: `src/domain/plans.ts` no repositório do Manager (PRO, Gestor e o teste grátis).
- **Balcão**: `DEFAULT_PRICES` em `bot/config.py` no repositório do Balcão (o "a partir de" é o Viajante mensal).

## Contato

WhatsApp e Telegram da seção "Fale com a gente" são os mesmos de suporte do Balcão (SUPPORT_WHATSAPP e o canal).

## Motion Kit (assets/motion)

`gomilhasx-motion.css` e `gomilhasx-motion.js` são a fonte oficial do kit de animações da marca (sem dependências).
O Manager e o Balcão usam uma cópia com a mesma versão no cabeçalho: ao mudar aqui, suba a versão e copie para lá.
Classes: `gx-stage` + `data-gx-bg="network|grid|flow"` (fundo), `gx-reveal` (entrada), `gx-card`, `gx-btn`,
`gx-glow`, `gx-faq` e `data-gx-count` (contador, só com dado real). Tudo respeita prefers-reduced-motion.

## Ver localmente

```bash
python3 -m http.server 8000
```

Fonte Inter (SIL Open Font License) e ícones Lucide (ISC).
