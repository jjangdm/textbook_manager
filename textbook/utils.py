import os
import logging
import time
from django.conf import settings
from django.core.management import call_command


logger = logging.getLogger('backup')


def manage_backups(max_backups=5):
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith('.json')],
        key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
        reverse=True
    )
    
    while len(backups) > max_backups:
        os.remove(os.path.join(backup_dir, backups.pop()))

def backup_database():
    BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups')
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    timestamp = time.strftime('%Y%m%d-%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'db_backup_{timestamp}.json')

    with open(backup_file, 'w') as f:
        call_command('dumpdata', '--indent', '2', stdout=f)

    manage_backups()  # 백업 파일 관리 호출

    logger.info(f"Database backup created: {backup_file}")
    return f"Database backup created: {backup_file}"


def restore_database(backup_file):
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    full_path = os.path.join(backup_dir, backup_file)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Backup file not found: {full_path}")

    call_command('flush', '--noinput')  # 기존 데이터 삭제
    call_command('loaddata', backup_file)

    logger.info(f"Database restored from: {backup_file}")
    return f"Database restored from: {backup_file}"