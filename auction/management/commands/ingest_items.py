import json
from django.core.management.base import BaseCommand
from auction.models import Item, Category, User

class Command(BaseCommand):
    help = 'Ingest items from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='The path to the JSON file to be ingested')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        with open(file_path, 'r') as file:
            data = json.load(file)

        for item_data in data:
            try:
                user = User.objects.get(username=item_data['username'])
                category, created = Category.objects.get_or_create(name=item_data['category'])
                item = Item(
                    title=item_data['title'],
                    description=item_data['description'],
                    category=category,
                    user=user,
                    starting_price=item_data['starting_price']
                )
                item.save()
                self.stdout.write(self.style.SUCCESS(f"Successfully added item: {item.title}"))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User '{item_data['username']}' does not exist"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error adding item '{item_data['title']}': {str(e)}"))
