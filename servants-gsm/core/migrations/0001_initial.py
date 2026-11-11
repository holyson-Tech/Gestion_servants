from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Doc",
            fields=[
                ("id", models.CharField(max_length=160, primary_key=True, serialize=False)),
                ("data", models.JSONField()),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("updated_by", models.CharField(blank=True, max_length=150)),
            ],
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("user", models.CharField(max_length=150)),
                ("action", models.CharField(max_length=8)),
                ("doc_id", models.CharField(db_index=True, max_length=160)),
                ("data", models.JSONField(blank=True, null=True)),
            ],
            options={"ordering": ["-at"]},
        ),
    ]
