# Captura rápida (Épico 2) — setup dos workflows n8n

## Status atual

- ✅ **Captura por ATALHO: NO AR e testada** (workflow `EwhCapturaAtalho` ativo no
  n8n; segredo em `/root/.ewh-captura-segredo` na VPS; instruções do celular em
  `.plane-local/atalho-captura-ana.md`). Voz coberta pelo ditado nativo do iPhone.
- ⏸️ **Captura por WHATSAPP: em espera** — canal opcional; ativar apenas se o
  encaminhamento de mensagens fizer falta. Depende de escolher o número (decisão
  🔶 nº 4 do PRD). O passo a passo abaixo continua válido.
- ℹ️ Lição do deploy: o n8n 2.x exige `id` no JSON importado e `webhookId` no nó
  de webhook — sem `webhookId` o caminho registra malformado
  (`workflowId/nome%20do%20nó/path`). Os JSONs deste diretório já contêm ambos.
  Após importar/ativar via CLI, ciclar `n8n_editor` e `n8n_webhook` para o
  registro em `webhook_entity` ser refeito.

Estado em 26/08/2026:

- ✅ Token de API `n8n-captura` criado na produção (workspace `grupo-espacial-motel`,
  usuário Ana Beatriz). Recuperar o valor completo **na VPS**:
  ```bash
  ssh -i ~/.ssh/trademachine_vps root@72.60.254.32 \
    'docker exec plane-be-api-1 python manage.py shell -c \
     "from plane.db.models import APIToken; print(APIToken.objects.get(label=\"n8n-captura\").token)"'
  ```
- ✅ Projeto privado **"Captura — Ana Beatriz"** criado na produção
  (`id 1a84be32-f826-4a28-a99c-4f17cf36c20e`).
- ✅ Workflows prontos para importar: `captura-atalho.json`, `captura-whatsapp.json`.
- ⚠️ A Evolution API tem 5 instâncias antigas, **todas desconectadas** (`connecting`).
  A captura deve usar uma instância **nova e dedicada** — não reaproveitar as antigas.
- 🔶 Depende da decisão nº 4 do PRD: qual número de WhatsApp será o da captura.

## Passo a passo

### 1. Instância WhatsApp dedicada

```bash
# na VPS, com a apikey global da Evolution (env AUTHENTICATION_API_KEY):
curl -X POST https://evo.fisioterapia.cloud/instance/create \
  -H "apikey: $EVO_KEY" -H "Content-Type: application/json" \
  -d '{"instanceName": "easyworkhub-captura", "qrcode": true, "integration": "WHATSAPP-BAILEYS"}'
```

Escanear o QR com o número escolhido (decisão 🔶). Depois configurar o webhook da
instância apontando para o n8n, **somente** evento `messages.upsert`:

```bash
curl -X POST https://evo.fisioterapia.cloud/webhook/set/easyworkhub-captura \
  -H "apikey: $EVO_KEY" -H "Content-Type: application/json" \
  -d '{"webhook": {"enabled": true, "url": "https://n8nwebhook.fisioterapia.cloud/webhook/ewh-whatsapp", "events": ["MESSAGES_UPSERT"]}}'
```

### 2. Importar e preencher os workflows

No editor do n8n (`n8neditor.fisioterapia.cloud`): **Import from file** → os dois JSONs.

Preencher os `TODO` (ficam todos em nós de configuração no início de cada fluxo):

| TODO | Onde conseguir |
|---|---|
| `TODO_plane_api_...` | comando do token acima |
| Telefone da Ana | formato `55DDDNÚMERO`, sem `+` e sem espaços |
| `TODO_APIKEY_EVOLUTION` | `docker exec <evolution> env \| grep AUTHENTICATION_API_KEY` |
| `TODO_OPENAI_KEY` | chave da OpenAI (Whisper) — decisão nº 5 do PRD |
| `TODO_segredo_...` | inventar string longa; vai também dentro do atalho do celular |

Ativar os dois workflows (toggle no topo).

### 3. Atalho no celular da Ana

**iOS (Atalhos):** novo atalho → "Solicitar entrada de texto" → "Obter conteúdo do
URL" (POST `https://n8nwebhook.fisioterapia.cloud/webhook/ewh-captura`, JSON:
`{"segredo": "...", "chave": "ana-2f8k", "texto": [Entrada]}`) → adicionar à tela
inicial. O mesmo atalho aparece na folha de compartilhamento e pode ir para o
botão de Ação/tela bloqueada.

**Android:** widget do app Atalhos/HTTP Shortcuts com o mesmo POST.

### 4. Testes de aceite (Épico 2 do PRD)

```bash
# texto via atalho (simulado):
curl -X POST https://n8nwebhook.fisioterapia.cloud/webhook/ewh-captura \
  -H "Content-Type: application/json" \
  -d '{"segredo": "...", "chave": "ana-2f8k", "texto": "Comprar mangueira nova para Rocket"}'
```

1. ✅ esperado: item aparece em "Captura — Ana Beatriz" com rodapé "Capturado pelo atalho • HH:MM".
2. WhatsApp texto: mandar mensagem do número da Ana → item criado + resposta "✅ Capturado: …".
3. WhatsApp áudio: mandar áudio → item com transcrição + "Capturado por voz • HH:MM".
4. Número desconhecido: silêncio total (nenhum item, nenhuma resposta).
5. Privacidade: projeto de captura invisível para outros membros.

## Decisões de projeto embutidas nos fluxos

- **Roteamento por remetente**, com token do próprio usuário → o item nasce com o
  autor certo e as permissões do Plane valem sozinhas.
- **Número desconhecido = silêncio** (não responde "não autorizado") — não revela
  a existência do fluxo a estranhos.
- **Grupos e mensagens nossas são ignorados** (`fromMe`, `@g.us`).
- **Áudio sem fala** vira item mesmo assim ("ouvir no WhatsApp") — capturar nunca falha.
- Novos usuários = nova entrada na tabela `USUARIOS` dos dois fluxos + projeto
  "Captura — {Nome}" + token próprio (mesmo padrão do da Ana).

## Rollback

Desativar os dois workflows no n8n. Nada a reverter no Plane.
