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

## Ver localmente

```bash
python3 -m http.server 8000
```

Fonte Inter (SIL Open Font License) e ícones Lucide (ISC).
