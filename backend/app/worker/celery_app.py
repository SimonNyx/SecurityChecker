from celery import Celery
from app.config import settings

celery_app = Celery("securitychecker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_always_eager = False
