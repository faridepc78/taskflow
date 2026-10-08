from django.db import migrations, models
import config.upload_paths


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_profile_created_at_profile_updated_at")]
    operations = [migrations.AlterField(
        model_name="profile", name="avatar",
        field=models.ImageField(blank=True, null=True, upload_to=config.upload_paths.avatar_upload_path),
    )]
