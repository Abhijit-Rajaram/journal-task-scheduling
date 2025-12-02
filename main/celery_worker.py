from celery import Celery
from celery.schedules import crontab
from config import settings
import asyncio
from database import SessionLocal
from email_utils import send_email
from datetime import date

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

# ------------ DATABASE QUERIES ---------------

async def get_today_tasks():
    async with SessionLocal() as session:
        result = await session.execute("""
            SELECT u.email, t.name, t.description
            FROM task_instance t
            JOIN user u ON t.user_id = u.id
            WHERE t.date = CURRENT_DATE
        """)
        return result.fetchall()


async def get_today_summary():
    async with SessionLocal() as session:
        result = await session.execute("""
            SELECT u.email, t.name, t.description, t.done
            FROM task_instance t
            JOIN user u ON t.user_id = u.id
            WHERE t.date = CURRENT_DATE
        """)
        return result.fetchall()


# ------------ EMAIL HTML BUILDERS -------------

def build_task_table(rows):
    table = ""
    for r in rows:
        table += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ccc">{r.name}</td>
            <td style="padding:8px;border:1px solid #ccc">{r.description}</td>
        </tr>
        """
    return table


def build_summary_table(rows):
    table = ""
    for r in rows:
        status = "<b style='color:green'>Completed</b>" if r.done else "<b style='color:red'>Pending</b>"
        table += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ccc">{r.name}</td>
            <td style="padding:8px;border:1px solid #ccc">{r.description}</td>
            <td style="padding:8px;border:1px solid #ccc'>{status}</td>
        </tr>
        """
    return table


# ------------ CELERY TASKS ---------------------
async def generate_daily_tasks():
    today = date.today()
    weekday = today.strftime("%a").lower()[:3]

    async with SessionLocal() as session:
        # Get all users
        result = await session.execute("SELECT id FROM user")
        users = result.fetchall()

        for user in users:
            user_id = user.id

            # Check if tasks for today already exist
            existing = await session.execute(
                f"SELECT id FROM task_instance WHERE user_id = {user_id} AND date = CURRENT_DATE"
            )
            if existing.first():
                continue

            # Get all templates for this user
            templates = await session.execute(
                f"SELECT id, name, description, frequency, weekdays, day_of_month, specific_date "
                f"FROM task_template WHERE user_id = {user_id}"
            )
            templates = templates.fetchall()

            for t in templates:
                # Frequency Rules (exact same as Flask)
                if t.frequency == "daily":
                    allowed = True

                elif t.frequency == "weekly":
                    days = (t.weekdays or "").split(",")
                    allowed = weekday in days

                elif t.frequency == "monthly":
                    allowed = (t.day_of_month == today.day)

                elif t.frequency == "date":
                    allowed = (t.specific_date == today)

                else:
                    allowed = False

                if not allowed:
                    continue

                # Insert task instance
                await session.execute(
                    """
                    INSERT INTO task_instance (user_id, template_id, name, description, date)
                    VALUES (:uid, :tid, :name, :desc, CURRENT_DATE)
                    """,
                    {
                        "uid": user_id,
                        "tid": t.id,
                        "name": t.name,
                        "desc": t.description
                    }
                )

        await session.commit()


@celery_app.task
def create_all_users_daily_tasks():
    asyncio.run(generate_daily_tasks())
    print("Daily tasks created for all users.")


@celery_app.task
def send_morning_tasks():
    rows = asyncio.run(get_today_tasks())

    users = {}
    for r in rows:
        users.setdefault(r.email, []).append(r)

    for email, tasks in users.items():
        html = f"""
        <h2>Your Tasks for Today</h2>
        <table style="border-collapse:collapse;width:100%">
            <tr style="background:#3498db;color:white">
                <th style="padding:10px;border:1px solid #ccc">Task</th>
                <th style="padding:10px;border:1px solid #ccc">Description</th>
            </tr>
            {build_task_table(tasks)}
        </table>
        """

        send_email("Today's Task List", html, email)

    print("Morning emails sent.")


@celery_app.task
def send_night_summary():
    rows = asyncio.run(get_today_summary())

    users = {}
    for r in rows:
        users.setdefault(r.email, []).append(r)

    for email, tasks in users.items():
        html = f"""
        <h2>Your Task Summary</h2>
        <table style="border-collapse:collapse;width:100%">
            <tr style="background:#2ecc71;color:white">
                <th style="padding:10px;border:1px solid #ccc">Task</th>
                <th style="padding:10px;border:1px solid #ccc">Description</th>
                <th style="padding:10px;border:1px solid #ccc">Status</th>
            </tr>
            {build_summary_table(tasks)}
        </table>
        """

        send_email("Today's Completed & Pending Tasks", html, email)

    print("Night summary emails sent.")



# ------------ CELERY BEAT SCHEDULE -------------

celery_app.conf.beat_schedule = {
    "create_daily_tasks_midnight": {
        "task": "worker.create_all_users_daily_tasks",
        "schedule": crontab(hour=0, minute=1),
    },
    "morning_tasks": {
        "task": "worker.send_morning_tasks",
        "schedule": crontab(hour=4, minute=0),
    },
    "night_summary": {
        "task": "worker.send_night_summary",
        "schedule": crontab(hour=23, minute=0),
    },
}


celery_app.conf.timezone = settings.TIMEZONE
