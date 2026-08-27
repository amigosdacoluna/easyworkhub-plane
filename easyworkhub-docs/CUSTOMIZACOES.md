# Registro de customizações do fork (`ewh-custom`)

Exigência do brief (§18 e §24): toda customização documentada, com ponto de
patch, motivo e estratégia de reaplicação em atualizações do Plane.

**Base:** Plane Community `v1.4.2` (idêntica à produção no momento do fork).
**Branch:** `ewh-custom`. **Processo de atualização:** a cada release upstream →
`git rebase` desta branch sobre a nova tag → CI builda → homologação → troca de
tag na produção. Rollback = voltar a tag de imagem anterior.

---

## C1 — Filtros relativos de data (Épico 4)

**Motivo:** Views "Hoje", "Atrasadas", "Próximos 7 dias" que continuam corretas
sem edição manual (brief §15). O backend já resolvia tokens relativos por
consulta; faltavam granularidade em dias, tokens de calendário e a UI.

| Arquivo                                                  | Mudança                                                                                                                                                                                                                                                                                                                                                          |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/plane/utils/issue_filters.py`                  | + tokens dinâmicos (`today/tomorrow/yesterday/this_week/next_week/this_month/no_date` × `exact/after/before`); + termo `days` com intervalos `next`/`last`; regex estendida para `days`. **Todas as datas calculadas no fuso de negócio** (`EWH_BUSINESS_TZ`, padrão `America/Sao_Paulo`) — corrige o "hoje" virando às 21h (UTC-3). Blocos marcados com `EWH:`. |
| `packages/constants/src/filter.ts`                       | `DATE_AFTER_FILTER_OPTIONS` reescrita com 14 presets em português (Hoje, Amanhã, Ontem, Atrasadas, Esta semana, Próxima semana, Este mês, Próximos 7/30 dias, Últimos 7 dias, A partir de amanhã, Sem data, + 2 legados traduzidos).                                                                                                                             |
| `packages/utils/src/datetime.ts`                         | `parseDateFilter`/`checkDateCriteria` reescritos para semântica de **intervalo** (`{after?, before?, noDate?}`), espelhando o backend — o filtro local (atualização ao vivo do quadro) entende os tokens novos. Assinatura antiga removida.                                                                                                                      |
| `apps/web/core/store/issue/helpers/base-issues-utils.ts` | Adaptado à nova assinatura; item sem data agora **casa** com o filtro "Sem data" em vez de ser descartado antes da avaliação.                                                                                                                                                                                                                                    |

**Semântica dos tokens novos** (fonte da verdade: backend):

| Token                      | Resolve para                         |
| -------------------------- | ------------------------------------ |
| `today;exact;fromnow`      | `[hoje, hoje]`                       |
| `yesterday;before;fromnow` | `≤ ontem` (Atrasadas)                |
| `this_week;exact;fromnow`  | `[segunda, domingo]` da semana atual |
| `this_month;exact;fromnow` | `[dia 1, último dia]` do mês atual   |
| `7_days;next;fromnow`      | `[hoje, hoje+7]`                     |
| `7_days;last;fromnow`      | `[hoje−7, hoje]`                     |
| `no_date;exact;fromnow`    | `campo IS NULL`                      |

**Compatibilidade:** tokens legados (`2_weeks;after;fromnow`) e datas exatas
(`2026-09-15;after`) intocados — verificado por teste (10 casos, 26/08/2026).

### C1b — Descoberta: dois sistemas de filtro convivem no v1.4.2

A tela de Work Items e as Views modernas usam o sistema **rich filters**
(expressão JSON no parâmetro `filters`, chips com operador), e NÃO as listas
`DATE_AFTER_FILTER_OPTIONS` do sistema legado (que seguem em ciclos, módulos e
perfil). O C1 sozinho não bastava. Extensão aplicada:

| Arquivo                                                                  | Mudança                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/api/plane/utils/filters/filterset.py`                              | `start_date`/`target_date` (e `__exact`) viram `CharFilter` com método EWH: token com `;` → resolvido pelo MESMO `date_filter()` do C1 (um só resolvedor para os dois sistemas); data pura → igualdade; valor inválido → no-op (nunca 500). `__range` (calendário) intocado. |
| `packages/utils/src/rich-filters/factories/configs/properties/shared.ts` | O operador "é" (EXACT) dos filtros de data virou **select de 12 períodos relativos em português** (`EWH_RELATIVE_DATE_PRESETS`), com os mesmos tokens de 3 partes. Datas absolutas ficam no operador de intervalo (RANGE). Chip mostra o rótulo do preset automaticamente.   |

Verificado por teste no endpoint real (7 casos: Hoje/Atrasadas/Próx.7d/Sem
data/data pura/range/lixo — 27/08/2026).

**Risco de rebase:** baixo. `issue_filters.py` muda raramente; blocos EWH são
aditivos. `filter.ts` (constantes) é lista de dados. O ponto mais sensível é
`datetime.ts`/`base-issues-utils.ts` se o upstream refatorar o filtro local.

**Config:** `EWH_BUSINESS_TZ` (env, opcional; padrão America/Sao_Paulo).

---

## Pendentes (próximos nesta branch)

- C2 — Interface 100% pt-BR, lote 1 (Épico 6)
- C3 — Alertas internos de prazo via Celery beat (Épico 5b)
- C4 — Horário opcional nas tarefas, colunas aditivas (Épico 7)

## Infra

- `.github/workflows/ewh-build-images.yml` — CI: builda as 5 imagens (amd64) e
  publica no GHCR com tags `ewh-latest` + `ewh-<sha>` a cada push na branch.
