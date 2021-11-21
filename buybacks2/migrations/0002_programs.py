from django.db import migrations, models

from ..validators import validate_brokerage


class Migration(migrations.Migration):

    dependencies = [
        ("buybacks2", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Program",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "corporation",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="+",
                        to="buybacks2.corporation",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=100,
                    ),
                ),
            ],
            options={
                "default_permissions": (),
            },
        ),
        migrations.CreateModel(
            name="ProgramItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="+",
                        to="buybacks2.program",
                    ),
                ),
                (
                    "item_type",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="+",
                        to="eveuniverse.evetype",
                    ),
                ),
                (
                    "brokerage",
                    models.IntegerField(
                        help_text="Jita max buy - x%",
                        validators=[validate_brokerage],
                    ),
                ),
                (
                    "use_refined_value",
                    models.BooleanField(
                        help_text="If ore, calculate on top of refined value",
                    ),
                ),
            ],
            options={
                "default_permissions": (),
            },
        ),
        migrations.CreateModel(
            name="ProgramLocation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="+",
                        to="buybacks2.program",
                    ),
                ),
                (
                    "office",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="+",
                        to="buybacks2.office",
                    ),
                ),
            ],
            options={
                "default_permissions": (),
            },
        ),
        migrations.AlterUniqueTogether(
            name="ProgramItem",
            unique_together={("program", "item_type")},
        ),
        migrations.AlterUniqueTogether(
            name="ProgramLocation",
            unique_together={("program", "office")},
        ),
    ]
