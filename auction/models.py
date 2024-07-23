from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    shipping_address = models.TextField()
    credit_card_info = models.CharField(max_length=255, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='auction_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='auction_users_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )


class Category(models.Model):
    name = models.CharField(max_length=255)
    parent_category = models.ForeignKey('self', null=True, blank=True, related_name='subcategories',
                                        on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class ItemCondition(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Item(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, related_name='items', on_delete=models.PROTECT)
    condition = models.ForeignKey(ItemCondition, related_name='items', on_delete=models.PROTECT, null=True)
    user = models.ForeignKey(User, related_name='items', on_delete=models.PROTECT)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_time = models.DateTimeField(default=timezone.now, editable=False)
    end_time = models.DateTimeField()
    sold_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    buyer = models.ForeignKey(User, related_name='purchased_items', null=True, blank=True, on_delete=models.SET_NULL)
    sold = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.id and not self.start_time:
            self.start_time = timezone.now()
        if not self.id and not self.end_time:
            self.end_time = self.start_time + timedelta(days=7)

        # Mark as sold if the auction has ended and the item is not already marked as sold
        if self.end_time <= timezone.now() and not self.sold:
            self.sold = True
            highest_bid = self.bids.order_by('-amount').first()
            if highest_bid:
                self.sold_price = highest_bid.amount
                self.buyer = highest_bid.user

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
class Bid(models.Model):
    item = models.ForeignKey(Item, related_name='bids', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='bids', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount}"
