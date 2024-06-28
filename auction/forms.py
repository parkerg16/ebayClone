from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Item, Category, Bid


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email_address', 'password1', 'password2', 'shipping_address',
                  'credit_card_info']


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'category', 'starting_price', 'image']

    def __init__(self, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)
        item = kwargs.get('instance')
        if item and item.bids.exists():
            self.fields.pop('starting_price')
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']