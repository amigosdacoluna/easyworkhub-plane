# EWH (C5): motor de recorrência nativo — substitui o motor n8n.
#
# A tarefa-MOLDE é uma tarefa comum com `ewh_recurrence` definido pela UI
# ({"frequencia": "diaria"|"semanal"|"mensal", "ativo": true, "ultima": ...}).
# Todo dia às 5h (Brasília):
#   1. se o prazo do molde é hoje (ou já passou — catch-up), gera a OCORRÊNCIA
#      do dia: cópia independente com sufixo " · DD/MM", herdando descrição,
#      prioridade, responsáveis, etiquetas e hora; estado inicial = "A fazer".
#   2. avança o prazo do molde para a PRÓXIMA data do padrão — o molde nunca
#      fica atrasado e o quadro sempre mostra a próxima execução.
# Semanal repete no dia da semana do prazo do molde; mensal no dia do mês
# (meses curtos: último dia). Idempotente por `ultima` (1 ocorrência/dia).

import os
from datetime import timedelta

from celery import shared_task
from dateutil.relativedelta import relativedelta

from plane.db.models import Issue, IssueAssignee, IssueLabel, State
from plane.utils.exception_logger import log_exception
from plane.utils.issue_filters import ewh_business_today


def _proxima_data(atual, frequencia):
    if frequencia == "diaria":
        return atual + timedelta(days=1)
    if frequencia == "semanal":
        return atual + timedelta(days=7)
    if frequencia == "mensal":
        return atual + relativedelta(months=1)
    return None


def _gerar_ocorrencia(molde, hoje):
    estado = (
        State.objects.filter(project=molde.project, group="unstarted").order_by("sequence").first()
        or molde.state
    )
    ocorrencia = Issue.objects.create(
        project=molde.project,
        workspace=molde.workspace,
        name=f"{molde.name} · {hoje.strftime('%d/%m')}",
        description_html=molde.description_html or "<p></p>",
        priority=molde.priority,
        state=estado,
        target_date=hoje,
        target_time=molde.target_time,
        start_time=molde.start_time,
        created_by=molde.created_by,
    )
    IssueAssignee.objects.bulk_create([
        IssueAssignee(
            issue=ocorrencia, assignee=a.assignee, project=molde.project,
            workspace=molde.workspace, created_by=molde.created_by,
        )
        for a in molde.issue_assignee.all()
    ])
    IssueLabel.objects.bulk_create([
        IssueLabel(
            issue=ocorrencia, label=lb.label, project=molde.project,
            workspace=molde.workspace, created_by=molde.created_by,
        )
        for lb in molde.label_issue.all()
    ])
    return ocorrencia


@shared_task
def ewh_recurrence_task():
    if os.environ.get("EWH_RECURRENCE", "1") in ("0", "false", "False"):
        return "desligado por ambiente"
    try:
        hoje = ewh_business_today()
        moldes = Issue.objects.filter(
            ewh_recurrence__ativo=True,
            target_date__isnull=False,
            archived_at__isnull=True,
            is_draft=False,
        ).select_related("project", "workspace", "state")

        geradas, resumo = 0, []
        for molde in moldes:
            cfg = molde.ewh_recurrence or {}
            freq = cfg.get("frequencia")
            if freq not in ("diaria", "semanal", "mensal"):
                continue
            if cfg.get("ultima") == hoje.isoformat():
                continue  # já gerou hoje (idempotência)
            if molde.target_date > hoje:
                continue  # próxima execução ainda no futuro

            ocorrencia = _gerar_ocorrencia(molde, hoje)
            geradas += 1
            resumo.append(ocorrencia.name[:60])

            # avança o molde para a próxima data FUTURA (catch-up sem inundar)
            proxima = molde.target_date
            while proxima <= hoje:
                proxima = _proxima_data(proxima, freq)
            cfg["ultima"] = hoje.isoformat()
            molde.ewh_recurrence = cfg
            molde.target_date = proxima
            molde.save(update_fields=["ewh_recurrence", "target_date"])

        return f"ocorrências geradas: {geradas} | {resumo}"
    except Exception as e:
        log_exception(e)
        raise
