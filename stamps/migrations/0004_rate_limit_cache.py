from django.core.management import call_command
from django.db import migrations


def create_cache(apps, schema_editor):
    call_command('createcachetable', 'stampede_cache', database=schema_editor.connection.alias)


class Migration(migrations.Migration):
    dependencies = [('stamps', '0003_alter_stampparticipation_unique_together')]
    operations = [migrations.RunPython(create_cache, migrations.RunPython.noop)]