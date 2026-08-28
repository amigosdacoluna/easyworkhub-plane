# EWH (C5): recorrência definida na própria tarefa — coluna aditiva.
# REBASE: manter a cadeia ewh_0001 → ewh_0002; só a ewh_0001 aponta para upstream.
# Rollback: coluna órfã é inerte (null e ignorada pelo código oficial).

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "ewh_0001_issue_time_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="issue",
            name="ewh_recurrence",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
