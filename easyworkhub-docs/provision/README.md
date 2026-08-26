# Provisionamento — Grupo Espacial

Aplica a arquitetura de projetos do PRD (§5) via API pública do EasyWorkHub.

## Estado

- ✅ Testado na instância **local** (`easy-work-hub` @ localhost:8080) em 26/08/2026:
  7 projetos, 7 estados renomeados/criados por projeto, etiquetas por contexto,
  Intake ativo só em Manutenção e Compras, Visualizações ativas em todos.
- ✅ Idempotente: segunda execução = 0 mudanças.
- 🔶 **Não aplicado em produção** — aguarda aprovação da arquitetura pela Diretoria.

## Uso

```bash
pip3 install requests pyyaml

# simular (não altera nada):
python3 provision.py arquitetura.yaml \
  --base-url https://plane.easyworkhub.com.br \
  --workspace grupo-espacial-motel \
  --token plane_api_xxx \
  --dry-run

# aplicar: remover --dry-run
```

O token é criado no Django shell do container da API (usuário de serviço):

```python
from plane.db.models import APIToken, User, Workspace
u = User.objects.get(email="<email do responsável>")
w = Workspace.objects.get(slug="grupo-espacial-motel")
t, _ = APIToken.objects.get_or_create(user=u, workspace=w, label="provision",
                                      defaults={"user_type": 1})
print(t.token)
```

## Garantias

- **Nunca apaga nada.** Estados/etiquetas fora do padrão são apenas reportados (`⚠`).
- Estados default do Plane (Backlog/Todo/…) são **renomeados** para a nomenclatura
  do Grupo — não duplicados.
- Respeita o rate limit da API (pausa entre escritas; espera e repete em 429).
- Projetos existentes com o mesmo nome são adotados e completados, não recriados.

## Depois de aplicar em produção (manual, uma vez)

1. Criar as Views nativas (brief §7) em cada projeto — a API pública não cria views.
2. Ajustar ícone/capa dos projetos (estético).
3. Convidar os usuários a cada projeto (Story 1.8).
4. Excluir ou arquivar os projetos de teste ("Projeto Empresa", "Rotina diária") —
   **decisão da Ana Beatriz/Diretoria**, não do script.
