# PRD — EasyWorkHub · Grupo Espacial Motéis

**Produto:** EasyWorkHub (Plane Community `v1.4.2` self-hosted)
**Instância:** `https://plane.easyworkhub.com.br/grupo-espacial-motel/`
**Responsável técnico:** Lucas
**Origem:** BRIEF-EASYWORKHUB-CONFIGURACAO-E-DESENVOLVIMENTO-GRUPO-ESPACIAL v2
**Data:** 26/08/2026
**Status:** Draft — aguardando validação da Diretoria nos pontos marcados 🔶

---

## 1. Visão e objetivo

Transformar o EasyWorkHub no sistema operacional de tarefas do Grupo Espacial
(unidades Espacial, Rocket e Pérola), cobrindo o fluxo:

**CAPTURAR → ORGANIZAR → EXECUTAR → ACOMPANHAR**

O sistema deve eliminar a dependência de memória, papel, WhatsApp como repositório
de pendências, planilhas paralelas e cobranças manuais.

### Métricas de sucesso (do brief, seção 26)

| Métrica | Como verificar |
|---|---|
| Registrar demanda em segundos, do celular | Teste cronometrado: tela inicial → captura < 15s |
| Rotinas geradas automaticamente | Zero criação manual de tarefas recorrentes após config |
| Atrasos visíveis sem esforço | View "Atrasadas" correta em qualquer dia, sem edição |
| Notificações dentro do sistema | E-mail reduzido a menções/críticos |
| Interface em português | Navegação das telas principais sem inglês funcional |
| Rastreabilidade de solicitações | Toda demanda com histórico e autor |

---

## 2. Descobertas da auditoria de código

A auditoria do código-fonte (clonado, mesmo nível da instância) **corrige premissas
do brief** e muda o custo de vários itens:

| # | Descoberta | Impacto no plano |
|---|---|---|
| D1 | O backend **já suporta filtros relativos de data** (`X_weeks;after;fromnow`, resolvidos a cada consulta em `apps/api/plane/utils/issue_filters.py`). O que falta é: granularidade em **dias**, semântica "hoje/atrasadas", e a UI expor essas opções. | Filtros relativos caem de "desenvolvimento grande" para **patch pequeno e aditivo** (backend +~40 linhas, frontend novas opções em `packages/constants/src/filter.ts`). Views salvas guardam o token relativo, não a data — **já ficam dinâmicas por construção**. |
| D2 | O prazo é `target_date = models.DateField` (`apps/api/plane/db/models/issue.py:148`). | Converter para DateTime = migração destrutiva de alto risco. A estratégia certa para horário é **coluna aditiva** (`target_time` TimeField null), não conversão. |
| D3 | Recorrência **não existe em nenhum modelo** do core. | Confirmado. Mas ver D6. |
| D4 | Existe **modelo de Rascunho** (`DraftIssue`) e **API pública de Intake e Issues** (`apps/api/plane/api/views/`), acionável por Token de Acesso Pessoal. | Captura externa pode criar itens via API sem tocar no core. |
| D5 | O Celery Beat usa `DatabaseScheduler` com `beat_schedule` em `apps/api/plane/celery.py`. Não há tarefa de alerta de prazo. | Alertas internos = **tarefa aditiva** (1 arquivo novo em `bgtasks/` + 1 entrada no schedule). Não altera nada existente. |
| D6 | A VPS já roda **n8n** (com workers) e **Evolution API** (WhatsApp) na mesma rede Docker do EasyWorkHub. | Recorrência, captura por WhatsApp e lembretes podem ser implementados **fora do core**, com atualização do Plane sem impacto. Este é o maior ativo estratégico do projeto. |
| D7 | Os arquivos de tradução pt-BR estão **100% completos** (3.837/3.837 chaves em `packages/i18n/src/locales/pt-BR/`). O inglês residual visto na instância vem de **strings hardcoded nos componentes** (fora do sistema i18n) e de telas sem i18n (admin/god-mode). | O trabalho de tradução não é "traduzir arquivos" — é **internacionalizar strings hardcoded** e aplicar o glossário. Escopo diferente, mais cirúrgico. |
| D8 | Filtros "hoje" no backend usam `timezone.now().date()` em **UTC do servidor**. Para o Brasil (UTC-3), "hoje" viraria às 21h locais. | O patch de filtros relativos **deve calcular datas no fuso do usuário** (o perfil já tem `user_timezone`). Isso reforça a seção 9 do brief. |

---

## 3. Estratégia técnica em três camadas

Princípio (brief, seções 2 e 24): *não desenvolver o que a configuração resolve;
preferir extensão a alteração do núcleo; sobreviver a atualizações.*

```
┌───────────────────────────────────────────────────────────────┐
│ CAMADA 0 — CONFIGURAÇÃO NATIVA                                │
│ Sem código. Projetos, estados, etiquetas, views, notificações │
│ → Épico 1                                                     │
├───────────────────────────────────────────────────────────────┤
│ CAMADA 1 — AUTOMAÇÃO EXTERNA (n8n + Evolution + API pública)  │
│ Zero mudança no core. Sobrevive a qualquer atualização.       │
│ → Épicos 2 (captura), 3 (recorrência), 5a (lembretes)         │
├───────────────────────────────────────────────────────────────┤
│ CAMADA 2 — FORK CONTROLADO (patches mínimos e versionados)    │
│ Branch própria + CI de build de imagens. Só o que exige core. │
│ → Épicos 4 (filtros), 5b (alertas in-app), 6 (pt-BR),         │
│   7 (horário)                                                 │
└───────────────────────────────────────────────────────────────┘
```

Regra de decisão: um item só sobe de camada quando a camada inferior
comprovadamente não atende ao critério de aceite.

---

## 4. Épicos

### ÉPICO 1 — Fundação por configuração (Camada 0)

**Objetivo:** implantar a Parte A do brief inteira, sem código, antes de qualquer
desenvolvimento.

**Stories:**

| ID | Story | Critério de aceite | Prio |
|---|---|---|---|
| 1.1 | Corrigir fuso horário de todos os perfis para `America/Sao_Paulo` (Brasília) e incluir no checklist de onboarding de cada novo usuário | Nenhum perfil em UTC; datas do calendário batem com o dia local | Essencial |
| 1.2 | 🔶 Definir arquitetura de projetos com a Diretoria (por unidade? por setor? matriz sugerida na seção 5 abaixo) | Documento de arquitetura aprovado | Essencial |
| 1.3 | Criar projetos oficiais e configurar estados padrão (Ideias/A avaliar · A fazer · Em andamento · Aguardando terceiro · Aguardando diretoria · Concluído · Cancelado) 🔶 nomenclatura a validar | Estados idênticos em todos os projetos oficiais | Essencial |
| 1.4 | Criar taxonomia de etiquetas (UNIDADE / SETOR / TIPO conforme brief §6), aplicando em cada projeto só as pertinentes | Sem etiquetas duplicadas ou divergentes entre projetos | Alta |
| 1.5 | Criar Views nativas que não dependem de data relativa: Por responsável, Aguardando diretoria, Aguardando terceiro, Solicitações pendentes, Minhas tarefas | Views salvas e visíveis aos membros certos | Essencial |
| 1.6 | Configurar notificações: caixa interna ativa para atribuições/menções/comentários; e-mail reduzido a menções diretas e críticos | Config aplicada e documentada por papel | Essencial |
| 1.7 | Definir Pages iniciais (procedimentos curtos, checklists de apoio) e onde o Intake fica ativo (manutenção, compras, solicitações à diretoria) | Pages criadas; Intake ativo apenas nos projetos definidos | Alta |
| 1.8 | Convidar usuários aos projetos corretos, com papel adequado (Admin/Member/Guest) | Cada usuário vê somente o que deve | Essencial |

**Dependências:** nenhuma. **Esforço:** 1–2 dias de configuração + sessão de
validação com a Diretoria. **Risco:** baixo.
**Bloqueia:** todos os épicos seguintes (padronização é pré-requisito de
automação e analytics).

---

### ÉPICO 2 — Captura rápida por texto e voz (Camada 1)

**Objetivo (brief §13):** registrar uma demanda em segundos, do celular, sem abrir
o sistema. Sem perguntar projeto, responsável, prioridade, prazo, etiqueta ou
estado. Destino: caixa de entrada **privada** do usuário. *Captura não é tarefa
oficial.*

**Solução proposta — três portas de entrada, um destino:**

```
① WhatsApp (texto ou áudio) ─┐
② Atalho iOS / Android ──────┼─→ n8n (roteia por remetente,
③ "Compartilhar para EWH" ───┘    transcreve áudio se preciso)
                                       │
                                       ▼
                       Projeto privado "📥 Captura — {Nome}"
                       (1 por usuário, só ele + diretoria vê)
                       item criado via API pública com Token
```

- **① WhatsApp** é a porta principal: a Evolution API já está instalada. O usuário
  manda texto ou **áudio** para o número do sistema; o n8n identifica o remetente
  pelo telefone (tabela de mapeamento telefone→token/projeto), transcreve o áudio
  (Whisper API ou equivalente) e cria o item com o texto + rótulo de origem
  (`Capturado por voz • 14:32`). Responde no WhatsApp com "✅ Capturado".
- **② Atalho** (Atalhos do iOS / widget-atalho Android) chama um webhook n8n com o
  texto — dá captura pela tela inicial e, no iOS, pela tela bloqueada via botão de
  Ação/widget de Atalho.
- **③ Compartilhar** usa o mesmo atalho como destino da folha de compartilhamento.
- **Triagem:** o usuário abre seu projeto de captura no EasyWorkHub, e move/completa
  o que virar tarefa oficial (nativo: mover item entre projetos preserva histórico).

**Por que não usar Rascunhos (DraftIssue)?** O modelo existe (D4), mas não tem
endpoint na API pública — só na API interna de sessão. Usar API interna criaria
acoplamento frágil. O projeto privado por usuário entrega o mesmo efeito
(privacidade + triagem) com API estável. Reavaliar se a API pública ganhar drafts.

**Devolutiva técnica (brief §25):**

| Campo | Resposta |
|---|---|
| Onde implementa | n8n (workflows) + Evolution API + 1 projeto privado por usuário |
| Altera core? | **Não.** Zero patch |
| Dependências | Evolution API conectada a um número dedicado; serviço de transcrição (custo ~US$0,006/min de áudio); tokens de acesso pessoais |
| Impacto em updates do Plane | Nenhum (usa API pública estável) |
| Risco | Baixo. Ponto de atenção: instabilidade ocasional de sessão WhatsApp na Evolution (mitigar com monitor + reconexão) |
| Esforço | 3–5 dias (workflows, mapeamento de usuários, atalhos, testes com áudio real de motel — ruído de ambiente) |
| Desktop | Captura nativa no próprio EWH (tecla C) já resolve |
| Android / iOS | WhatsApp (idêntico nos dois) + atalho por plataforma |
| Rollback | Desativar workflows n8n; nada a reverter no Plane |

**Critérios de aceite:**
1. Da tela inicial do celular, capturar por texto em < 15 segundos.
2. Mandar áudio de WhatsApp e encontrar o texto transcrito na captura privada em < 1 min.
3. Item capturado não aparece em nenhum projeto oficial até ser triado.
4. Outro usuário comum não vê a captura de ninguém.

---

### ÉPICO 3 — Recorrência (Camada 1)

**Objetivo (brief §14):** rotina configurada uma vez gera ocorrências novas e
independentes ("Verificar apartamentos interditados" → uma tarefa nova por dia,
sem reabrir nem apagar a de ontem).

**Solução proposta:** motor de recorrência no n8n.

- **Definição das rotinas:** planilha de rotinas (n8n Data Table) com colunas:
  título, descrição, checklist, projeto, responsável, prioridade, etiquetas,
  frequência (`diaria | dias_semana:seg,qua | semanal | mensal:dia5 | anual |
  cada:3d`), hora de criação, início, término opcional, ativo (sim/não).
- **Execução:** workflow agendado roda 1×/dia (e 1×/hora para frequências com
  hora), calcula o que vence, e cria cada ocorrência via API pública — título com
  sufixo de data quando fizer sentido ("· 26/08"), copiando descrição, checklist
  (subitens), responsável, prioridade e etiquetas (campos confirmados na API).
- **Idempotência:** o workflow marca a última execução por rotina; reprocessar o
  dia não duplica tarefas.
- **Gestão pelo usuário-chave:** documento-Page "Rotinas do Grupo" lista as rotinas
  ativas; alterações são feitas por Lucas/gestor treinado na tabela do n8n
  (10 min de treino). Uma UI própria de rotinas fica para a Fase 2, se o volume
  justificar.

**Devolutiva técnica:**

| Campo | Resposta |
|---|---|
| Onde | n8n (1 workflow + 1 Data Table) |
| Altera core? | **Não** |
| Dependências | Token de serviço; Épico 1 concluído (projetos/etiquetas estáveis) |
| Impacto em updates | Nenhum |
| Risco | Baixo. Atenção: fuso horário do cálculo (usar America/Sao_Paulo no n8n, D8) |
| Esforço | 2–4 dias incluindo testes de todas as frequências |
| Rollback | Desativar workflow; ocorrências já criadas permanecem (correto) |

**Critérios de aceite:**
1. Rotina diária gera tarefa nova a cada dia; concluir a de hoje não afeta a de ontem.
2. Todas as frequências mínimas do brief funcionam (diária, dias da semana, semanal, mensal, anual, a cada X, início, término).
3. Ocorrência criada tem responsável, prioridade, etiquetas e checklist da rotina.
4. Reexecutar o workflow no mesmo dia não duplica tarefas.

---

### ÉPICO 4 — Filtros relativos de data (Camada 2 · patch pequeno)

**Objetivo (brief §15):** Views como "Hoje", "Atrasadas", "Próximos 7 dias" que
continuam corretas amanhã sem edição manual.

**Base existente (D1):** o backend já resolve tokens relativos
(`2_weeks;after;fromnow`) **no momento da consulta** — a mecânica de view dinâmica
já existe. Falta: granularidade `days`, semântica "hoje/ontem/amanhã/sem data",
e a UI expor os presets.

**Solução proposta (fork, patch aditivo):**

1. **Backend** — `apps/api/plane/utils/issue_filters.py`: adicionar termo `days`
   ao `string_date_filter` e tokens especiais (`today`, `yesterday`, `tomorrow`,
   `no_date`), calculando datas **no fuso do usuário** (D8), não no UTC do servidor.
2. **Frontend** — `packages/constants/src/filter.ts` (+ componente de filtro):
   presets em português: Hoje · Amanhã · Ontem · Esta semana · Próxima semana ·
   Este mês · Próximos 7 dias · Próximos 30 dias · Últimos 7 dias · Antes de hoje
   (Atrasadas) · Depois de hoje · Sem data · Próximos X dias.
3. **Views padrão** — criar as Views "Hoje", "Atrasadas", "Próximos 7 dias" nos
   projetos oficiais (config, após o patch).

**Devolutiva técnica:**

| Campo | Resposta |
|---|---|
| Onde | Fork: `issue_filters.py` (~40 linhas aditivas) + constantes/UI de filtro |
| Altera core? | Sim, porém **aditivo** — não muda comportamento existente |
| Dependências | Estratégia de fork/build (Épico 6 compartilha a mesma) |
| Impacto em updates | Baixo: pontos de patch pequenos e estáveis entre versões; rebase documentado |
| Risco | Baixo/médio (o cálculo por fuso do usuário exige teste na virada de dia) |
| Esforço | 3–5 dias com testes |
| Rollback | Reverter para imagem oficial `stable`; views relativas param de filtrar mas nada quebra |

**Critérios de aceite:**
1. View "Atrasadas" mostra itens com prazo < hoje **no fuso de Brasília**, inclusive entre 21h e 0h.
2. View "Próximos 7 dias" salva hoje continua correta em qualquer data futura, sem edição.
3. Filtros novos aparecem em português no seletor de filtros.

---

### ÉPICO 5 — Alertas internos de prazo (Camadas 1 + 2)

**Objetivo (brief §16):** avisos de "vence amanhã / vence hoje / atrasada /
atrasada há X dias / urgente", priorizando a caixa de entrada interna, sem spam,
sem depender de e-mail.

**Solução em duas etapas:**

- **5a (Camada 1, imediata):** workflow n8n diário (ex.: 7h) consulta a API por
  itens vencendo/vencidos por responsável e envia **um resumo único** por usuário
  via WhatsApp (Evolution): "Bom dia! Você tem 2 tarefas para hoje e 1 atrasada:
  …" — um toque no link abre o item. Sem spam: 1 mensagem/dia, só para quem tem
  pendência, com opt-out por usuário.
- **5b (Camada 2, junto do fork):** tarefa Celery aditiva
  (`bgtasks/deadline_notification_task.py` + entrada no `beat_schedule`, D5) que
  cria **notificações na caixa interna** para: vence amanhã, vence hoje, ficou
  atrasada, atrasada há X dias. Configuração de limiar por workspace via
  variável de ambiente nesta fase.

**Devolutiva técnica (5b):**

| Campo | Resposta |
|---|---|
| Onde | Fork: 1 arquivo novo em `bgtasks/` + ~6 linhas no `celery.py` |
| Altera core? | Aditivo (arquivo novo; nenhuma alteração de modelo) |
| Risco | Baixo. Deduplicação necessária (não notificar 2× o mesmo evento) |
| Esforço | 5a: 1–2 dias · 5b: 3–4 dias |
| Rollback | 5a: desligar workflow · 5b: remover a entrada do schedule |

**Critérios de aceite:**
1. Usuário com tarefa vencendo hoje recebe aviso interno (5b) e/ou resumo matinal (5a) — nunca mais de 1 resumo/dia.
2. Item que muda de prazo não gera aviso duplicado.
3. Usuário sem pendências não recebe nada.
4. Avisos respeitam permissões (ninguém é notificado de item que não vê).

---

### ÉPICO 6 — Interface 100% em português (Camada 2)

**Objetivo (brief §18):** eliminar inglês funcional das telas de uso diário e
administração, com o glossário do Grupo (Work item→**Tarefa**,
Assignee→**Responsável**, Target date→**Prazo**, Views→**Visualizações**,
Intake→**Recepção**).

**Diagnóstico (D7):** os arquivos pt-BR já estão completos. O inglês residual vem
de **strings hardcoded** nos componentes (ex.: "First day of the week", "Filters",
"More", "Search commands", barras de onboarding) e de telas sem i18n (admin).
O trabalho real é internacionalizar essas strings e aplicar o glossário.

**Solução proposta:**

1. **Auditoria guiada por telas** (não por grep cego): navegar as jornadas
   principais (login → onboarding → projeto → tarefa → views → configurações →
   admin) capturando cada string em inglês, priorizada por visibilidade.
2. **Patches:** mover strings hardcoded para o i18n (`packages/i18n`) e completar
   o pt-BR; onde a chave já existe, apenas revisar com o glossário.
3. **Glossário do Grupo:** camada de revisão dos termos nas chaves pt-BR — isso é
   edição de arquivos de tradução, com baixa chance de conflito em rebase.
4. **Admin/god-mode:** segunda prioridade; traduzir jornadas que gestores usam
   (membros, autenticação, e-mail), não 100% do painel na primeira leva.
5. **Contribuição upstream:** patches de i18n são candidatos naturais a PR para o
   Plane — cada PR aceito é manutenção que deixamos de carregar.

**Estratégia de fork e atualização (responde brief §18 "requisito técnico" — vale
para os Épicos 4, 5b, 6 e 7):**

- Repositório fork `easyworkhub/plane`, branch `ewh-custom` baseada na **última
  tag estável**; cada customização = commits isolados e documentados
  (`docs/CUSTOMIZACOES.md` no fork: o quê, onde, por quê, como reaplicar).
- **Build:** GitHub Actions constrói as imagens (`amd64`) e publica em registry
  próprio (GHCR ou o registry local já existente na VPS). *Não* compilar na VPS
  (2 vCPU compartilhados).
- **Atualização do Plane:** a cada release upstream → rebase da `ewh-custom` →
  CI → teste em stack de homologação → troca de tag na produção. Rollback =
  voltar a tag anterior da imagem (bancos intactos, pois patches não alteram
  schema exceto Épico 7, que tem migração própria).

**Devolutiva técnica:**

| Campo | Resposta |
|---|---|
| Onde | Fork: `packages/i18n/` + componentes com strings hardcoded |
| Altera core? | Sim — mudanças pequenas e espalhadas (i18n), sem lógica |
| Impacto em updates | Médio: é o épico com mais pontos de contato; mitigado por PRs upstream e pelo processo de rebase |
| Risco | Baixo por mudança; o risco é de **volume** (estimativa por lote) |
| Esforço | Lote 1 (jornadas de usuário): 4–6 dias · Lote 2 (admin): 2–4 dias |
| Rollback | Imagem anterior |

**Critérios de aceite:**
1. Jornada completa (entrar → criar tarefa → mover no quadro → filtrar → configurar perfil) sem nenhuma string funcional em inglês.
2. Glossário aplicado de forma consistente (nunca "Work item" e "Item de trabalho" convivendo).
3. `docs/CUSTOMIZACOES.md` lista cada string/arquivo alterado.

---

### ÉPICO 7 — Horário nas tarefas (Camada 2 · maior risco do Fase 1)

**Objetivo (brief §17):** hora de início e de vencimento **opcionais**; tarefas
comuns seguem só com data.

**Análise de opções (decisão técnica central):**

| Opção | Descrição | Veredito |
|---|---|---|
| A. Converter `target_date` para DateTime | Migração destrutiva, toca serializers, filtros, ordenação, exportação, todos os pickers | ❌ Rejeitada — viola brief §24 (alteração profunda do núcleo) |
| B. **Colunas aditivas** `start_time` / `target_time` (TimeField, null) no modelo Issue + exibição/edição na UI | Migração aditiva própria e reversível; comportamento atual intocado quando null | ✅ **Recomendada** |
| C. Convenção no título ("⏰ 14h") + lembrete n8n | Zero código, zero garantia de consistência | Aceitável só como interim antes do fork existir |

**Solução proposta (Opção B):**

1. Migração aditiva com prefixo próprio (`ewh_0001_issue_time_fields`) — não
   conflita com numeração upstream.
2. Serializer/API expõem os campos novos (aditivo).
3. UI: campo de hora opcional ao lado do seletor de data; badge de hora no cartão
   e na lista quando preenchido; ordenação secundária por hora dentro do dia.
4. Integrações: recorrência (Épico 3) pode preencher hora; lembretes (Épico 5)
   passam a considerar hora quando existir; Google Calendar (Fase 2) usa esses
   campos como gatilho de sincronização.

**Devolutiva técnica:**

| Campo | Resposta |
|---|---|
| Onde | Fork: modelo Issue (+2 colunas null), serializers, componentes de data |
| Altera core? | Sim — o único épico com **migração de banco** |
| Impacto em updates | Médio: migração aditiva com namespace próprio raramente conflita; UI de data é o ponto de rebase mais sensível |
| Risco | Médio. Exige homologação antes de produção |
| Esforço | 6–10 dias |
| Rollback | Reverter imagem; colunas extras ficam órfãs no banco **sem efeito** (null e ignoradas pelo código oficial) — remoção posterior opcional |

**Critérios de aceite:**
1. Tarefa sem hora se comporta exatamente como hoje.
2. Tarefa com hora exibe a hora no detalhe, no cartão e na lista.
3. Duas tarefas no mesmo dia ordenam pela hora.
4. Exportação CSV/Excel inclui as colunas de hora.

---

## 5. 🔶 Proposta de arquitetura de projetos (para discussão — Story 1.2)

Insumo para a decisão da Diretoria; não é decisão tomada:

```
Workspace: Grupo Espacial
├── 🏨 Operação Espacial      ─┐  1 projeto por unidade:
├── 🚀 Operação Rocket         ├─ rotinas e demandas do dia a dia
├── 🐚 Operação Pérola        ─┘  (etiquetas de SETOR dentro deles)
├── 🔧 Manutenção (Intake ON)     transversal, triagem ativa
├── 🛒 Compras (Intake ON)        transversal, triagem ativa
├── 🏛️ Diretoria (privado)        decisões, aprovações, confidencial
├── 📣 Marketing                  transversal
└── 📥 Captura — {um por usuário, privado}   (Épico 2)
```

Racional: espelha como as pessoas pensam ("problema da Rocket" / "pedido de
compra"), mantém Intake só onde há triagem real (brief §11) e isola o
confidencial. Etiqueta de UNIDADE só nos projetos transversais (nos de unidade é
redundante — brief §6).

---

## 6. Roadmap e dependências

```
SEMANA 1        SEMANAS 2–3           SEMANAS 3–5              SEMANAS 5–8
─────────────   ───────────────────   ──────────────────────   ─────────────────
ÉPICO 1         ÉPICO 2 (captura)     ÉPICO 4 (filtros)        ÉPICO 7 (horário)
config nativa   ÉPICO 3 (recorrênc.)  ÉPICO 6 lote 1 (pt-BR)   ÉPICO 6 lote 2
+ arquitetura   ÉPICO 5a (resumo      ÉPICO 5b (alertas        homologação
  aprovada 🔶     WhatsApp)             in-app)                + implantação
                Camada 1 — sem fork   ← fork nasce aqui →
```

- Épicos 2, 3 e 5a são **paralelos** entre si e não dependem do fork — valor na
  mão do usuário já na semana 2.
- O fork nasce uma única vez e carrega 4, 5b, 6 e 7 juntos.
- Fase 2 (fora deste PRD, reavaliar com uso real — brief §§19–21): Google
  Calendar para tarefas com horário (via n8n, viabilizada pelo Épico 7), campos
  personalizados, automações condicionais, UI de gestão de rotinas.

**Estimativa total Fase 1:** 24–40 dias úteis de desenvolvimento + configuração,
com as entregas da Camada 1 concentradas nas duas primeiras semanas.

---

## 7. Riscos gerais

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Sessão WhatsApp (Evolution) cair e capturas se perderem | Média | Alto | Monitor de conexão + alerta; atalho iOS/Android como canal redundante; n8n guarda fila de não-entregues |
| Rebase do fork custoso a cada release do Plane | Média | Médio | Patches mínimos e documentados; PRs de i18n para upstream; homologação antes de produção |
| VPS (2 vCPU compartilhados) sob carga com transcrição + builds | Média | Médio | Builds no GitHub Actions, nunca na VPS; transcrição via API externa (não local) |
| Adoção baixa (equipe volta ao WhatsApp) | Média | Alto | Captura *pelo* WhatsApp reduz a fricção da mudança; resumo matinal cria hábito de retorno ao sistema; treinar com o manual existente |
| Cálculo de datas em UTC gerar "hoje" errado | Alta se ignorado | Alto | D8 tratada como requisito nos Épicos 3, 4 e 5; testes na janela 21h–0h |
| Escopo de tradução crescer sem fim | Média | Médio | Lotes fechados por jornada; critério = telas de uso real, não 100% do produto |

---

## 8. Fora de escopo (Fase 1)

- Kit Inicial / instalador de templates (brief §22 — retirado; config manual única).
- Google Calendar, campos personalizados, automações condicionais (Fase 2).
- App móvel nativo (o PWA + WhatsApp cobrem o celular).
- UI própria para gestão de rotinas (tabela n8n + Page documentada nesta fase).

---

## 9. Pontos abertos para decisão 🔶

1. **Arquitetura de projetos** (seção 5) — Diretoria.
2. **Nomenclatura final dos estados** (Story 1.3) — Diretoria.
3. **Taxonomia final de etiquetas** (Story 1.4) — junto da arquitetura.
4. **Número de WhatsApp dedicado à captura** — usar linha existente na Evolution ou contratar chip novo?
5. **Serviço de transcrição** — OpenAI Whisper API (maduro) vs. Groq (mais barato/rápido); ambos ~centavos por áudio.
6. **Repositório do fork** — GitHub privado (Actions grátis limitado) ou público (Actions ilimitado; o Plane é AGPL, fork público é natural e obriga publicar fontes das modificações de qualquer forma, dado que há usuários externos acessando o serviço).
