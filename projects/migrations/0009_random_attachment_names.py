from django.db import migrations, models
import config.upload_paths


class Migration(migrations.Migration):
    dependencies = [("projects", "0008_category_owner_and_owner_name_constraint")]
    operations = [migrations.AlterField(
        model_name="taskattachment", name="file",
        field=models.FileField(upload_to=config.upload_paths.attachment_upload_path),
    )]
