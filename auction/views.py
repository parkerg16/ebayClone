from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .forms import ItemForm, BidForm, RegistrationForm
from .models import Item, Category
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout


def home(request):
    categories = Category.objects.all()
    category_items = {}
    for category in categories:
        items = Item.objects.filter(category=category).order_by('-start_time')[:4]
        for item in items:
            highest_bid = item.bids.order_by('-amount').first()
            item.highest_bid = highest_bid.amount if highest_bid else item.starting_price
        category_items[category] = items
    return render(request, 'auction/home.html', {'category_items': category_items})


@login_required
def user_items(request):
    items = Item.objects.filter(user=request.user)
    for item in items:
        highest_bid = item.bids.order_by('-amount').first()
        item.highest_bid = highest_bid.amount if highest_bid else None
    return render(request, 'auction/user_items.html', {'items': items})


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    has_bids = item.bids.exists()  # Check if there are any bids on the item

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('user_items')
    else:
        form = ItemForm(instance=item)

    return render(request, 'auction/edit_item.html', {'form': form, 'item': item, 'has_bids': has_bids})


def custom_logout_view(request):
    logout(request)
    return redirect('home')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'auction/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                print("Authentication failed")
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = AuthenticationForm()
    return render(request, 'auction/login.html', {'form': form})


@login_required
def submit_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            return redirect('home')
    else:
        form = ItemForm()
    return render(request, 'auction/submit_item.html', {'form': form})


@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if item.user != request.user:
        return HttpResponseForbidden("You are not allowed to delete this item.")

    if request.method == 'POST':
        item.delete()
        return redirect('home')

    return render(request, 'auction/delete_item_confirm.html', {'item': item})


@login_required
def place_bid(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.user == item.user:
        return redirect('item_detail', item_id=item.id)

    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.user = request.user
            bid.item = item

            highest_bid = item.bids.order_by('-amount').first()
            if highest_bid and bid.amount <= highest_bid.amount:
                form.add_error('amount', 'Bid must be higher than the current highest bid.')
            elif not highest_bid and bid.amount <= item.starting_price:
                form.add_error('amount', 'Bid must be higher than the starting price.')

            if not form.errors:
                bid.save()
                return redirect('item_detail', item_id=item.id)
    else:
        form = BidForm()

    return render(request, 'auction/place_bid.html', {'form': form, 'item': item})


def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    bids = item.bids.all()
    highest_bid = bids.order_by('-amount').first()
    bid_delta = 5

    # Determine the initial bid amount and ensure it is an integer
    if highest_bid:
        initial_bid_amount = int(highest_bid.amount + bid_delta)
    else:
        initial_bid_amount = int(item.starting_price + bid_delta)

    if request.method == 'POST':
        form = BidForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.user = request.user
            bid.item = item

            if request.user == item.user:
                messages.error(request, 'You cannot bid on your own item.')
            elif highest_bid and bid.amount <= highest_bid.amount:
                messages.error(request, 'Bid must be higher than the current highest bid.')
            elif not highest_bid and bid.amount <= item.starting_price:
                messages.error(request, 'Bid must be higher than the starting price.')
            else:
                bid.save()
                messages.success(request, 'Your bid has been placed successfully.')
                return redirect('item_detail', item_id=item.id)
    else:
        form = BidForm(initial={'amount': initial_bid_amount})

    return render(request, 'auction/item_detail.html', {
        'item': item,
        'bids': bids,
        'form': form,
        'highest_bid': highest_bid
    })

def item_list(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    items = Item.objects.filter(category=category)
    items_with_bids = []

    for item in items:
        highest_bid = item.bids.order_by('-amount').first()
        items_with_bids.append({
            'item': item,
            'highest_bid': highest_bid.amount if highest_bid else None
        })

    return render(request, 'auction/item_list.html', {'category': category, 'items_with_bids': items_with_bids})
