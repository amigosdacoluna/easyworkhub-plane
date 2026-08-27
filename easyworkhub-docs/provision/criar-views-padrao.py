# Cria as Views padrão dinâmicas em todos os projetos oficiais (Épico 4).
# Requer as imagens do fork ewh-custom rodando (tokens relativos no backend).
#
# Uso (no servidor):
#   docker cp criar-views-padrao.py plane-be-api-1:/tmp/
#   docker exec plane-be-api-1 python manage.py shell -c "exec(open('/tmp/criar-views-padrao.py').read())"

import json

from django.test import Client

from plane.db.models import IssueView, Project, User

DONO = "anabeatrizcarvalho10@gmail.com"
WORKSPACE = "grupo-espacial-motel"
IDENTIFICADORES = ["ESP", "RCK", "PER", "MNT", "CMP", "DIR", "MKT"]

# Nome, expressão rich (resolvida a cada consulta) — Views dinâmicas
VIEWS = [
    ("📅 Hoje", {"and": [{"target_date__exact": "today;exact;fromnow"}]}),
    ("🔴 Atrasadas", {"and": [{"target_date__exact": "yesterday;before;fromnow"}]}),
    ("📆 Próximos 7 dias", {"and": [{"target_date__exact": "7_days;next;fromnow"}]}),
]

client = Client()
client.force_login(User.objects.get(email=DONO))

for ident in IDENTIFICADORES:
    try:
        projeto = Project.objects.get(workspace__slug=WORKSPACE, identifier=ident)
    except Project.DoesNotExist:
        print(f"[{ident}] projeto não existe — pulado")
        continue
    existentes = set(
        IssueView.objects.filter(project=projeto).values_list("name", flat=True)
    )
    for nome, expressao in VIEWS:
        if nome in existentes:
            print(f"[{ident}] '{nome}' já existe")
            continue
        resposta = client.post(
            f"/api/workspaces/{WORKSPACE}/projects/{projeto.id}/views/",
            data=json.dumps({"name": nome, "rich_filters": expressao}),
            content_type="application/json",
        )
        print(f"[{ident}] '{nome}' -> HTTP {resposta.status_code}")
