import sqlite3
import os
import shutil
import schedule
import time
import pytz
from datetime import datetime, timedelta
import logging
import gzip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='server/static/backup/backup.log'
)
logger = logging.getLogger(__name__)

class BackupHandler:
    def __init__(self, db_path='devproject.db', backup_dir='server/static/backup'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.paris_tz = pytz.timezone('Europe/Paris')
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self):
        """Create a compressed backup of the database"""
        try:
            # Create timestamped backup filename
            timestamp = datetime.now(self.paris_tz).strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(self.backup_dir, f'backup_{timestamp}.db.gz')
            
            # Connect to database and create backup
            with sqlite3.connect(self.db_path) as conn:
                # Create a temporary backup file
                temp_backup = f'{self.db_path}.backup'
                conn.execute(f"VACUUM INTO '{temp_backup}'")
                
                # Compress the backup
                with open(temp_backup, 'rb') as f_in:
                    with gzip.open(backup_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove temporary file
                os.remove(temp_backup)
            
            logger.info(f"Successfully created backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return False

    def schedule_backups(self):
        """Schedule weekly backups at 3:00 AM Paris time"""
        # Create a Paris time datetime for Monday at 3:00 AM
        now = datetime.now(self.paris_tz)
        next_monday = now + timedelta(days=(7 - now.weekday()))
        paris_time = self.paris_tz.localize(datetime(
            next_monday.year,
            next_monday.month,
            next_monday.day,
            3, 0, 0
        ))
        
        # Convert to local time
        local_time = paris_time.astimezone()
        local_hour = local_time.hour
        local_minute = local_time.minute
        
        schedule.every().monday.at(f"{local_hour:02d}:{local_minute:02d}").do(self.create_backup)
        logger.info(f"Scheduled weekly backups for every Monday at {local_hour:02d}:{local_minute:02d} local time (3:00 AM Paris time)")

    def run_scheduler(self):
        """Run the backup scheduler continuously"""
        self.schedule_backups()
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

if __name__ == '__main__':
    handler = BackupHandler()
    handler.run_scheduler()
