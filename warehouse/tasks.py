# warehouse/tasks.py
import logging

import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10, ignore_result=True)
def sync_book_with_shop(self, book_id):
    from warehouse.models import Book

    try:
        book = Book.objects.get(pk=book_id)
    except Book.DoesNotExist:
        logger.warning("Book %s no longer exists, skipping sync", book_id)
        return

    payload = {
        "title": book.title,
        "authors": book.authors,
        "category": book.category,
        "publisher": book.publisher,
        "published_year": book.published_year,
        "isbn": book.isbn,
    }

    try:
        response = requests.post(
            f"{settings.SHOP_SERVICE_URL}/api/v1/books/sync/",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        logger.warning("Shop service unreachable for book %s, retrying", book_id)
        raise self.retry(exc=None)
    except requests.exceptions.HTTPError as exc:
        logger.error("Shop service rejected book %s: %s", book_id, exc.response.text)
        return

    logger.info("Book %s (isbn=%s) synced to shop", book_id, book.isbn)