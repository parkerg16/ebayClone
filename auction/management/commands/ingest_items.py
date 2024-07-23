import json
import os
from django.core.management.base import BaseCommand
from auction.models import Item, Category, User, ItemCondition, Bid
from django.core.files import File
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from random import sample, choice
from decimal import Decimal

class Command(BaseCommand):
    help = 'Ingest items and users from JSON files'

    def handle(self, *args, **kwargs):
        base_path = os.path.dirname(__file__)
        items_file_path = os.path.join(base_path, 'test.json')
        users_file_path = os.path.join(base_path, 'users.json')

        # Load users from JSON file
        with open(users_file_path, 'r') as users_file:
            users_data = json.load(users_file)

        for user_data in users_data:
            User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'shipping_address': user_data['shipping_address']
                }
            )

        # Load items from JSON file
        with open(items_file_path, 'r') as items_file:
            items_data = json.load(items_file)

        items = []
        for item_data in items_data:
            try:
                user = User.objects.get(username=item_data['username'])
                category, created = Category.objects.get_or_create(name=item_data['category'])
                condition, created = ItemCondition.objects.get_or_create(title=item_data['condition'])

                start_time = parse_datetime(item_data['start_time'])
                end_time = parse_datetime(item_data['end_time'])

                item = Item(
                    title=item_data['title'],
                    description=item_data['description'],
                    category=category,
                    user=user,
                    condition=condition,
                    starting_price=Decimal(item_data['starting_price']),
                    start_time=start_time,
                    end_time=end_time,
                    sold=item_data['sold']
                )

                # Handle the image file
                image_path = item_data.get('image')
                if image_path and os.path.exists(image_path):
                    with open(image_path, 'rb') as image_file:
                        item.image.save(os.path.basename(image_path), File(image_file), save=False)

                item.save()
                items.append(item)
                self.stdout.write(self.style.SUCCESS(f"Successfully added item: {item.title}"))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User '{item_data['username']}' does not exist"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error adding item '{item_data['title']}': {str(e)}"))

        # Mark half of the items as sold
        sold_items = sample(items, len(items) // 2)
        for item in sold_items:
            buyer = choice(User.objects.exclude(username=item.user.username).filter(username__startswith='user'))
            highest_bid = Bid.objects.create(item=item, user=buyer, amount=item.starting_price + Decimal(10))
            item.sold_price = highest_bid.amount
            item.buyer = highest_bid.user
            item.sold = True
            item.save()
            self.stdout.write(self.style.SUCCESS(f"Marked item as sold: {item.title} with buyer: {buyer.username}"))
