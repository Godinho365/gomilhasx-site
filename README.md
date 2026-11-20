# gomilhasx-site

Site institucional da GONORTE em https://gomilhasx.com: apresenta o GO Manager e o GO Balcão e os planos de cada um.

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
- `leia:` no artigo monta o quadro "Leia também" no fim do texto: páginas do site (`/para-viajantes/`, `/para-milheiros/`,
  `/para-agencias/`, `/calculadora-custo-do-milheiro/`, `/planilha-de-milhas/`, `/seguranca/`) e/ou `manager`, `balcao`.
- Links para o Manager e o Balcão: todo `<a>` para `manager.gonorte.com.br` ou `balcao.gomilhasx.com` leva
  `data-utm="identificador_do_botao"` na fonte (ex.: `hero_manager`, `planos_gestor`, `rodape_balcao`). O gerador troca o
  atributo por `?utm_source=gonorte.com.br&utm_medium=site&utm_content=<identificador>`, mantendo os parâmetros que o link já
  tem (`plano`, `periodo`...). Sem `data-utm` a geração para com erro, exceto nos artigos (vira `blog_<slug>`), nas páginas de
  privacidade e termos (ficam sem UTM) e em links que já trazem `utm_source`.
- `_fontes/paginas/404.html` gera o `404.html` da raiz (fora do sitemap, `noindex`, sem canonical). O Caddy só mostra essa
  página com um `handle_errors` no bloco `gomilhasx.com` (veja abaixo).
- O gerador também refaz `sitemap.xml`. A checagem do CI (`.github/scripts/checar_site.py`) confere todas as páginas e avisa se
  alguma página não foi gerada de novo depois de mudar a fonte.
- Estilos em `assets/site.css` e `assets/motion/gomilhasx-motion.css`: o gerador põe os dois (sem comentários) num `<style>`
  dentro de cada página, para a primeira pintura não esperar outro arquivo. Mudou o CSS, gere as páginas de novo.
  `assets/lead.css` (só o modal do Balcão) carrega sem bloquear. Animações em `assets/site-motion.js` (as páginas usam a
  versão do arquivo no endereço, então a mudança aparece na hora).
- Imagens: fotos (`assets/fotos/`) e telas (`assets/telas/`) ganham `srcset` automático com as versões menores de
  `assets/r/` (lista em `assets/imagens.json`). Na fonte, ponha `sizes="..."` com a largura em que a imagem aparece
  (sem `sizes`: foto = `100vw`, tela = `(max-width: 767px) 280px, 360px`); `loading="lazy"` em tudo que está fora da
  primeira dobra e `fetchpriority="high"` na imagem principal do topo (o `preload:` da página repete o mesmo srcset).
  Trocou ou acrescentou uma foto/tela? Gere as versões e depois as páginas:

  ```bash
  /home/deploy/balcao_gomilhasx-app/.venv/bin/python ferramentas/otimizar_imagens.py   # precisa de Pillow, fontTools e brotli
  python3 ferramentas/gerar_site.py
  ```

  O mesmo script refaz `assets/inter-marca.woff2` (Inter só com as letras do nome da marca e os símbolos que caem nela).
- Novas páginas precisam ser liberadas no Caddy do Manager (`docker/Caddyfile`, bloco `gomilhasx.com`, matcher `@site`).
- O simulador de transferência bonificada busca `/api/milheiro-hoje` (agregados do GO Balcão, `bot/milheiro_hoje.py` no
  repositório do Balcão) para sugerir a mediana do programa de destino como preço de venda. O Caddy repassa esse caminho
  para o `balcao-bot:8080`, como faz com `/api/lead*`; sem o repasse ou sem dados suficientes, a sugestão só não aparece.
- Página de erro: para o `404.html` aparecer nos endereços que não existem dentro do site (ex.: `/blog/nao-existe/`), o bloco
  `gomilhasx.com` do Caddyfile precisa de:

  ```caddy
  handle_errors 404 {
  	root * /srv/institucional
  	rewrite * /404.html
  	header Cache-Control "no-cache"
  	file_server
  }
  ```
- Celular: em telas de até 767px, `site-motion.js` não divide os títulos, não acende o parágrafo com a rolagem e não faz
  parallax; o CSS tira o desfoque de fundo (`backdrop-filter`) do cabeçalho e dos cartões. Animações contínuas fora da tela
  ficam pausadas (classe `.sm-pausa`) em qualquer tela.

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
