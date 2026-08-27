# EWH (Épico 7): horário opcional nas tarefas — colunas aditivas e reversíveis.
#
# ATENÇÃO NO REBASE: quando o upstream adicionar novas migrations ao app `db`,
# atualizar `dependencies` para a última migration upstream, senão o Django
# acusa múltiplos nós-folha. Este é o ÚNICO ajuste necessário.
#
# Rollback de imagem: as colunas ficam órfãs no banco sem efeito algum
# (null e ignoradas pelo código oficial). Remoção opcional:
#   ALTER TABLE issues DROP COLUMN start_time, DROP COLUMN target_time;

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0122_alter_draftissue_assignees_alter_issue_assignees_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="issue",
            name="start_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="issue",
            name="target_time",
            field=models.TimeField(blank=True, null=True),
        ),
    ]
