import logging
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import joinedload
from app.db.session import SessionLocal
from app.models.tasks import Task
from app.services.email_service import send_email
from app.core.config import settings

# Configure logging to show time and message
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_reminders():
    logger.info("🚀 Background reminder service started...")
    logger.info(f"Checking for tasks within a {settings.REMINDER_WINDOW_MINUTES} minute window.")
    
    while True:
        db = SessionLocal()
        try:
            # 1. Get current time in UTC
            now = datetime.utcnow()
            # 2. Define the future boundary (e.g., now + 10 mins)
            window = now + timedelta(minutes=settings.REMINDER_WINDOW_MINUTES)

            # Debug logs to help you see what the server is thinking
            logger.info(f"Heartbeat: Checking DB at UTC {now.strftime('%H:%M:%S')}")

            # 3. Query tasks
            # .options(joinedload(Task.user)) ensures we get the email address efficiently
            tasks = db.query(Task).options(joinedload(Task.user)).filter(
                Task.due_date <= window,
                Task.due_date >= now,  # Ensures we don't spam for expired tasks
                Task.reminder_sent == False,
                Task.status != 2        # 2 = Completed
            ).all()

            if tasks:
                logger.info(f"🎯 Found {len(tasks)} eligible task(s) for reminders.")

            for task in tasks:
                try:
                    if not task.user or not task.user.email:
                        logger.warning(f"⚠️ Task {task.id} has no valid user email. Skipping.")
                        continue

                    logger.info(f"📧 Sending email for '{task.title}' to {task.user.email}")
                    
                    send_email(
                        to=task.user.email,
                        subject="⏰ Task Reminder",
                        body=f"Hi! Just a reminder that your task '{task.title}' is due at {task.due_date.strftime('%Y-%m-%d %H:%M')} (UTC)."
                    )
                    
                    # 4. Mark as sent and commit immediately for this task
                    task.reminder_sent = True
                    db.add(task)
                    db.commit()
                    logger.info(f"✅ Successfully updated 'reminder_sent' for Task ID: {task.id}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to send email for Task ID {task.id}: {str(e)}")
                    db.rollback() # Rollback only this task's status change if email failed

        except Exception as e:
            logger.error(f"❌ Critical Database error in reminder loop: {str(e)}")
            db.rollback()
        finally:
            db.close()
            
        # 5. Wait for 60 seconds before checking again
        time.sleep(60)

if __name__ == "__main__":
    run_reminders()