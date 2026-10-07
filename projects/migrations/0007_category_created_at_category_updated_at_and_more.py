from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0006_activity_changes_activity_subject_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="category",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="taskattachment",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
