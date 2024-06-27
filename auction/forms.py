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
        fields = ['title', 'description', 'condition', 'category', 'image', 'starting_price']


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']
