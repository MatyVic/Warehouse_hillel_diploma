from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Book
from .tasks import sync_book_with_shop


@receiver(post_save, sender=Book)
def trigger_shop_sync(sender, instance, created, **kwargs):

    if created:
        sync_book_with_shop.delay(instance.id)
