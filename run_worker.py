from app.jobs.reminder_job import run_reminders
import logging
# ... other imports ...
from app.db.session import SessionLocal
from app.models.tasks import Task      # Import class
from app.models.user import UserTable  # Import class
from app.services.email_service import send_email
run_reminders()
