from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buybacks', '0002_programs'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'program_location',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='+',
                        to='buybacks.programlocation',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='+',
                        to='auth.user',
                    )
                ),
                (
                    'total',
                    models.PositiveBigIntegerField(
                        help_text='Total value of contract',
                    ),
                ),
                (
                    'items',
                    models.TextField(
                        help_text='JSON dump of item data',
                    ),
                ),
            ],
            options={
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                (
                    'id',
                    models.PositiveBigIntegerField(
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    'program',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='+',
                        to='buybacks.program',
                    ),
                ),
                (
                    'character',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='+',
                        to='authentication.characterownership',
                    )
                ),
                (
                    'total',
                    models.PositiveBigIntegerField(
                        help_text='Total value of contract',
                    ),
                ),
                (
                    'date',
                    models.DateTimeField(),
                ),
            ],
            options={
                'default_permissions': (),
            },
        ),
    ]
