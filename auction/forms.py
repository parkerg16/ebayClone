from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Item, Category, Bid


class RegistrationForm(UserCreationForm):
    real_name = forms.CharField(max_length=255)
    shipping_address = forms.CharField(widget=forms.Textarea)
    credit_card_info = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User
        fields = ['username', 'real_name', 'password1', 'password2', 'shipping_address', 'credit_card_info']

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'category', 'image', 'starting_price']


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']