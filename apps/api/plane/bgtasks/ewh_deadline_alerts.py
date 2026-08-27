# EWH: alertas internos de prazo (Épico 5b do PRD Grupo Espacial).
#
# Roda 1x/dia (beat) e cria notificações NA CAIXA INTERNA para os responsáveis:
#   - vence amanhã
#   - vence hoje
#   - atrasada (no 1º dia e depois a cada N dias — EWH_ALERT_OVERDUE_REPEAT_DAYS)
#
# Regras do brief §16: sem spam (dedupe por item+tipo+dia), sem depender de
# e-mail, respeita permissões (só responsáveis, que são membros do projeto).
# Desligável por ambiente: EWH_DEADLINE_ALERTS=0.

import os
from datetime import timedelta

from celery import shared_task

from plane.db.models import Issue, Notification
from plane.utils.exception_logger import log_exception
from plane.utils.issue_filters import ewh_business_today

SENDER_PREFIX = "in_app:ewh_deadline"


def _alert_title(kind, issue, dias_atraso=0):
    urgente = " ⚠ URGENTE" if issue.priority == "urgent" else ""
    nome = issue.name if len(issue.name) <= 80 else issue.name[:77] + "…"
    # EWH (Épico 7): inclui a hora quando a tarefa tiver horário definido
    hora = f" às {issue.target_time.strftime('%H:%M')}" if getattr(issue, "target_time", None) else ""
    if kind == "due_tomorrow":
        return f"⏰ Vence amanhã{hora}{urgente}: {nome}"
    if kind == "due_today":
        return f"📅 Vence hoje{hora}{urgente}: {nome}"
    plural = "dia" if dias_atraso == 1 else "dias"
    return f"🔴 Atrasada há {dias_atraso} {plural}{urgente}: {nome}"


def _notification_data(issue, titulo):
    return {
        "issue": {
            "id": str(issue.id),
            "name": str(issue.name),
            "identifier": str(issue.project.identifier),
            "sequence_id": issue.sequence_id,
            "state_name": issue.state.name if issue.state else "",
            "state_group": issue.state.group if issue.state else "",
        },
        "issue_activity": {
            "id": "",
            "verb": "ewh_deadline_alert",
            # field próprio, renderizado pelo mapa de conteúdo do frontend
            "field": "ewh_alert",
            "actor": "",
            "new_value": titulo,
            "old_value": "",
        },
    }


@shared_task
def ewh_deadline_alerts():
    if os.environ.get("EWH_DEADLINE_ALERTS", "1") in ("0", "false", "False"):
        return "desligado por ambiente"
    try:
        hoje = ewh_business_today()
        repeat = max(1, int(os.environ.get("EWH_ALERT_OVERDUE_REPEAT_DAYS", "3")))

        base = (
            Issue.objects.filter(
                target_date__isnull=False,
                archived_at__isnull=True,
                is_draft=False,
                assignees__isnull=False,
            )
            .exclude(state__group__in=["completed", "cancelled"])
            .select_related("project", "workspace", "state")
            .prefetch_related("assignees")
        )

        criadas, agora = 0, []
        for issue in base.filter(target_date__gte=hoje - timedelta(days=365), target_date__lte=hoje + timedelta(days=1)).distinct():
            if issue.target_date == hoje + timedelta(days=1):
                kind, dias = "due_tomorrow", 0
            elif issue.target_date == hoje:
                kind, dias = "due_today", 0
            else:
                dias = (hoje - issue.target_date).days
                # notifica no 1º dia de atraso e depois a cada `repeat` dias
                if (dias - 1) % repeat != 0:
                    continue
                kind = "overdue"

            sender = f"{SENDER_PREFIX}:{kind}:{hoje.isoformat()}"
            for user in issue.assignees.all():
                # dedupe: 1 alerta por item+tipo+dia+pessoa (idempotente)
                if Notification.objects.filter(
                    sender=sender, receiver=user, entity_identifier=issue.id
                ).exists():
                    continue
                agora.append(
                    Notification(
                        workspace=issue.workspace,
                        project=issue.project,
                        sender=sender,
                        receiver=user,
                        triggered_by=None,
                        entity_identifier=issue.id,
                        entity_name="issue",
                        title=(titulo := _alert_title(kind, issue, dias)),
                        data=_notification_data(issue, titulo),
                    )
                )
                criadas += 1

        Notification.objects.bulk_create(agora, batch_size=100)
        return f"alertas criados: {criadas}"
    except Exception as e:
        log_exception(e)
        raise
