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

Os preços são copiados dos apps. Ao mudar um preço lá, mude aqui também:

- **Manager**: `src/domain/plans.ts` no repositório MilhasX (`PLANS`, `ANNUAL_DISCOUNT_PCT`, `TRIAL_DAYS`). O preço anual por mês é o mensal com o desconto, arredondado.
- **Balcão**: `DEFAULT_PRICES` em `bot/config.py` no repositório do Balcão, que pode ser trocado no `.env` (`PRICE_<MÓDULO>_<PERÍODO>`).

## Ver localmente

```bash
python3 -m http.server 8000
```

Fonte Inter (SIL Open Font License) e ícones Lucide (ISC).
