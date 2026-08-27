# Recorrência de rotinas (Épico 3) — guia de gestão

**Status: NO AR e testada** (26/08/2026). Workflow `EwhRecorrencia` ativo no n8n,
agendado para **todo dia às 5h** (horário de Brasília, calculado no código —
independente do fuso do servidor).

Prova de funcionamento: a rotina "Verificar apartamentos interditados" gerou a
tarefa `Verificar apartamentos interditados · 26/08` no projeto Manutenção com
estado "A fazer", prioridade alta, prazo do dia e etiqueta Rotina. Segunda
execução no mesmo dia: **0 criadas** (trava de duplicação validada).

## Como editar as rotinas

1. Abrir `https://n8neditor.fisioterapia.cloud` → workflow **EWH · Recorrência de rotinas**
2. Duplo clique no nó **Motor de recorrência**
3. Editar **somente o bloco `ROTINAS`** no topo (o restante é o motor — não mexer)
4. Salvar. Vale a partir da próxima execução (5h do dia seguinte)

### Formato de uma rotina

```js
{
  id: 'verificar-interditados',   // único e estável — a trava de duplicação usa isso
  titulo: 'Verificar apartamentos interditados',
  descricao: 'Texto que aparece dentro da tarefa.',   // opcional
  projeto: 'MNT',                 // identificador real (EM RKT PEM MNT CMP DIR MKT)
  responsavel: 'email@dominio',   // opcional — a tarefa nasce atribuída (e os
                                  // alertas de prazo das 7h passam a valer!)
  hora: '07:30',                  // opcional — prazo com horário (aparece no
                                  // quadro e nos alertas: "Vence hoje às 07:30")
  prioridade: 'high',             // urgent | high | medium | low | none
  etiquetas: ['Rotina'],          // nomes exatos de etiquetas do projeto
  checklist: ['Passo 1', 'Passo 2'],   // opcional — vira lista na descrição
  frequencia: 'diaria',           // ver tabela abaixo
  inicio: '2026-09-01',           // opcional — não gera antes disso
  fim: null,                      // opcional — para de gerar depois disso
  sufixo_data: true,              // título ganha " · DD/MM"
  ativo: true                     // false = pausada sem apagar
}
```

### Frequências

| Valor                               | Significado                                                                           |
| ----------------------------------- | ------------------------------------------------------------------------------------- |
| `'diaria'`                          | todo dia                                                                              |
| `'dias_semana:seg,qua,sex'`         | dias específicos (dom seg ter qua qui sex sab)                                        |
| `'semanal:seg'`                     | uma vez por semana                                                                    |
| `'mensal:5'`                        | todo dia 5 (mês sem o dia — ex. 31 — não gera)                                        |
| `'anual:15/03'`                     | todo 15 de março                                                                      |
| `'cada:3d'` `'cada:2s'` `'cada:1m'` | a cada 3 dias / 2 semanas / 1 mês (≈30d), contando a partir de `inicio` (obrigatório) |

## Comportamento garantido (critérios do PRD)

- Cada ocorrência é uma **tarefa nova e independente** — concluir a de hoje não
  mexe na de ontem.
- **Trava de duplicação por dia**: reexecutar o workflow no mesmo dia não duplica
  (estado guardado no próprio workflow, por `id` de rotina).
- Tarefas nascem no estado **"A fazer"**, com prazo do dia e os campos da rotina.
- Autor das tarefas: conta da Ana (token `n8n-captura`).
- **Responsável e hora** (28/08/2026): a rotina "Verificar apartamentos
  interditados" nasce atribuída à Ana às 07:30. Validado em produção:
  tarefa criada com responsável correto e `target_time` preenchido.

## Testar manualmente (sem esperar as 5h)

```bash
ssh -i ~/.ssh/trademachine_vps root@72.60.254.32
EDITOR=$(docker ps --format "{{.Names}}" | grep n8n_editor | head -1)
docker exec -e N8N_RUNNERS_BROKER_PORT=5686 $EDITOR n8n execute --id=EwhRecorrencia
```

(a porta alternativa evita conflito com o broker do editor; o nó "Disparo manual"
existe no workflow exatamente para permitir execução por CLI)

## Avisos honestos

- **`id` é sagrado**: renomear o `id` de uma rotina zera a trava dela — no mesmo
  dia ela pode gerar de novo. Mudar título é livre; `id` não.
- `'cada:Xm'` usa mês aproximado de 30 dias — para "todo dia N do mês" use `'mensal:N'`.
- A primeira execução agendada real é **amanhã às 5h**; conferir se a tarefa
  `· 27/08` nasceu no Manutenção. Depois disso é rotina.
- Após editar rotinas pela UI do n8n não precisa reiniciar nada (a UI ativa/salva
  corretamente; o ciclo de serviços só é necessário quando se importa via CLI).
