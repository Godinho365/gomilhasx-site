# gomilhasx-site

Site institucional da GOMilhasX em https://gomilhasx.com: apresenta o GOMilhasX Manager e o GOMilhasX Balcão e os planos de cada um.

Site estático (HTML, CSS e imagens, sem build). No servidor fica em `/home/deploy/gomilhasx-app` e o Caddy do Manager
(projeto `milhasx`) monta a pasta em `/srv/institucional` e a serve direto no bloco `gomilhasx.com`.

## Publicar uma mudança

```bash
cd /home/deploy/gomilhasx-app && git pull
```

Não precisa reiniciar nada: o Caddy lê os arquivos a cada pedido (o HTML vai com `Cache-Control: no-cache`).

## Preços

A página mostra só um resumo (os planos completos ficam nos sites de cada produto). Os valores do resumo são
copiados dos apps; ao mudar um preço lá, confira a seção "Planos" do index.html:

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
