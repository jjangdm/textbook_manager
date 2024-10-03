# your_app/management/commands/backup_db.py

from django.core.management.base import BaseCommand
from textbook.utils import backup_database

class Command(BaseCommand):
    help = 'Backup the database'

    def handle(self, *args, **kwargs):
        result = backup_database()
        self.stdout.write(self.style.SUCCESS(result))