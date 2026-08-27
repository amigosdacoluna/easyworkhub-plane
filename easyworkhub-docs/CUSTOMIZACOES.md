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

## C2 — Interface pt-BR, lote 1 (Épico 6)

Strings hardcoded (fora do i18n) das jornadas principais, traduzidas direto:

| Superfície | Antes → Depois |
|---|---|
| Rótulos de filtro (`packages/utils/src/work-item-filters/configs/filters/*.ts`) | State→Estado, Assignees→Responsáveis, Priority→Prioridade, Label→Etiqueta, Cycle→Ciclo, Module→Módulo, Mentions→Menções, Created by→Criado por, State Group→Grupo de estado, Subscriber→Inscrito, Projects→Projetos |
| Linha de filtros (`rich-filters/filters-row.tsx`) | Clear all→Limpar tudo, Save view→Salvar visualização |
| Busca global (`top-nav-power-k.tsx`) | Search commands…→Buscar comandos… |
| Breadcrumb (`issues/header.tsx`) | Work Items→Itens de trabalho |
| Views (`*-layout-root.tsx`) | All work items→Todos os itens, Save as→Salvar como |
| Sidebar (`(projects)/sidebar.tsx` + wrapper + listas) | Projects→Projetos, More/Hide→Mais/Ocultar |
| Headers de view/módulo (`app/**/header.tsx`) | Add work item→Adicionar item |

Estratégia: substituição direta (não i18n) por serem strings fora do sistema de
tradução; candidatas a PR upstream com i18n formal depois. Risco de rebase:
baixo — strings pontuais.

## C3 — Alertas internos de prazo (Épico 5b)

| Arquivo | Mudança |
|---|---|
| `apps/api/plane/bgtasks/ewh_deadline_alerts.py` | **Novo** (aditivo). Task diária: cria notificações internas "vence amanhã / vence hoje / atrasada há X dias" para os responsáveis. Dedupe por item+tipo+dia (idempotente, testado); atraso renotificado a cada `EWH_ALERT_OVERDUE_REPEAT_DAYS` (padrão 3); desligável com `EWH_DEADLINE_ALERTS=0`; marca ⚠ URGENTE quando prioridade urgente; datas no fuso de negócio. |
| `apps/api/plane/celery.py` | +5 linhas: agenda `10:00 UTC` (= 7h Brasília). |
| `.../notification-card/content.tsx` | +7 linhas: handler do field `ewh_alert` no mapa de conteúdo (sem ele, o card não renderiza notificação sem ator). |

Testado: 4 alertas corretos (2 vence-hoje, 2 atrasadas), 2ª execução = 0 (dedupe).

## C4 — Horário opcional nas tarefas (Épico 7)

Opção B do PRD: **colunas aditivas**, sem tocar no `target_date`.

| Arquivo | Mudança |
|---|---|
| `apps/api/plane/db/models/issue.py` | +2 campos: `start_time`/`target_time` (TimeField, null) — null = comportamento original intacto |
| `apps/api/plane/db/migrations/ewh_0001_issue_time_fields.py` | **Migration própria** com instruções de rebase no cabeçalho (única manutenção: apontar `dependencies` para a última migration upstream) e de rollback (colunas órfãs são inertes) |
| `apps/api/plane/app/views/issue/base.py` + `utils/grouper.py` | Campos novos nas listas `.values()` das listagens (fluem para o quadro/lista) |
| `apps/api/plane/utils/order_queryset.py` | Ordenar por data desempata pela hora dentro do mesmo dia |
| `bgtasks/ewh_deadline_alerts.py` | Alerta inclui a hora: "Vence hoje às 14:30: …" |
| `packages/types/src/issues/issue.ts` | `start_time`/`target_time` no TIssue |
| `issue-detail/sidebar.tsx` | Campo de hora (input time nativo) ao lado das datas de início e vencimento; aparece só quando a data existe |
| `issue-layouts/properties/all-properties.tsx` | Chip "14:30" ao lado do chip de data no quadro/lista quando houver hora |

Serializers interno (`__all__`) e público (sem `fields`) expõem os campos
automaticamente — a API pública já aceita/retorna (testado: PATCH + GET).
A recorrência (n8n) pode definir `target_time` nas ocorrências.

## Pendentes (próximos nesta branch)

- C2 lote 2 — telas administrativas

## Infra

- `.github/workflows/ewh-build-images.yml` — CI: builda as 5 imagens (amd64) e
  publica no GHCR com tags `ewh-latest` + `ewh-<sha>` a cada push na branch.
