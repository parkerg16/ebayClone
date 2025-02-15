from io import BytesIO

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from django.contrib import messages
from django.utils import timezone
from datetime import datetime as dt

from reportlab.platypus import TableStyle, SimpleDocTemplate, Paragraph, Spacer, Table

from .forms import ItemForm, BidForm, RegistrationForm
from .models import Item, Category, User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout

def is_admin(user):
    return user.is_authenticated and user.is_staff

def home(request):
    categories = Category.objects.all()
    category_items = {}
    for category in categories:
        items = Item.objects.filter(category=category).order_by('-start_time')[:4]
        for item in items:
            highest_bid = item.bids.order_by('-amount').first()
            item.highest_bid = highest_bid.amount if highest_bid else item.starting_price
        category_items[category] = items
    return render(request, 'auction/home.html', {'category_items': category_items, 'timezone_now': timezone.now()})


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
            if highest_bid and bid.user == highest_bid.user:
                messages.error(request, 'You cannot outbid yourself.')
            elif highest_bid and bid.amount <= highest_bid.amount:
                messages.error(request, 'Bid must be higher than the current highest bid.')
            elif not highest_bid and bid.amount <= item.starting_price:
                messages.error(request, 'Bid must be higher than the starting price.')
            else:
                bid.save()
                return redirect('item_detail', item_id=item.id)
    else:
        form = BidForm()

    return render(request, 'auction/place_bid.html', {'form': form, 'item': item})


@login_required
def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    bids = item.bids.all()
    highest_bid = bids.order_by('-amount').first()

    # Check if the item has ended
    item_ended = item.end_time <= timezone.now()

    if request.method == 'POST' and not item_ended:
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
        form = BidForm()

    return render(request, 'auction/item_detail.html', {
        'item': item,
        'bids': bids,
        'form': form,
        'highest_bid': highest_bid,
        'item_ended': item_ended,
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

@user_passes_test(is_admin)
def report_items_on_sale(request):
    categories = Category.objects.all()
    selected_category_id = request.GET.get('category')

    items = Item.objects.filter(end_time__gt=timezone.now()).prefetch_related('bids')
    if selected_category_id:
        items = items.filter(category_id=int(selected_category_id))

    item_bids = []
    for item in items:
        highest_bid = item.bids.order_by('-amount').first()
        item_bids.append({
            'item': item,
            'highest_bid': highest_bid.amount if highest_bid else 'No bids'
        })

    return render(request, 'auction/report_items_on_sale.html', {
        'item_bids': item_bids,
        'categories': categories,
        'selected_category_id': int(selected_category_id) if selected_category_id else None,
    })


@user_passes_test(is_admin)
def download_items_on_sale_report(request):
    selected_category_id = request.GET.get('category')

    items = Item.objects.filter(end_time__gt=timezone.now()).prefetch_related('bids')
    if selected_category_id and selected_category_id != 'None':
        items = items.filter(category_id=int(selected_category_id))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="items_on_sale_report.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Items On Sale Report", styles['Title']))
    content.append(Spacer(1, 12))

    table_data = [['Title', 'Category', 'Starting Price', 'Current Bid', 'End Time']]
    for item in items:
        highest_bid = item.bids.order_by('-amount').first()
        table_data.append([
            item.title,
            item.category.name,
            f"${item.starting_price}",
            f"${highest_bid.amount}" if highest_bid else "No bids",
            item.end_time.strftime('%Y-%m-%d %H:%M:%S')
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-

1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.aliceblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    content.append(table)
    doc.build(content)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

@login_required
@user_passes_test(is_admin)
def report_items_bought(request):
    categories = Category.objects.all()
    selected_date = request.GET.get('date')
    selected_category_id = request.GET.get('category')

    if selected_date:
        selected_date = dt.strptime(selected_date, '%Y-%m-%d').date()

    items = Item.objects.filter(sold=True).exclude(sold_price__isnull=True)

    if selected_date:
        items = items.filter(end_time__date=selected_date)

    if selected_category_id:
        items = items.filter(category_id=int(selected_category_id))

    return render(request, 'auction/report_items_bought.html', {
        'items': items,
        'categories': categories,
        'selected_date': selected_date,
        'selected_category_id': int(selected_category_id) if selected_category_id else None,
    })

@login_required
@user_passes_test(is_admin)
def download_items_bought_report(request):
    selected_date = request.GET.get('date')
    selected_category_id = request.GET.get('category')

    items = Item.objects.filter(sold=True, sold_price__isnull=False, buyer__isnull=False).select_related('buyer', 'category', 'user')

    if selected_date:
        try:
            selected_date = dt.strptime(selected_date, '%Y-%m-%d').date()
            items = items.filter(end_time__date=selected_date)
        except ValueError:
            selected_date = None

    if selected_category_id and selected_category_id != 'None':
        items = items.filter(category_id=int(selected_category_id))

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="items_bought_report.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    title = "Items Bought Report"
    if selected_date:
        title += f" for {selected_date.strftime('%B %d, %Y')}"
    if selected_category_id and selected_category_id != 'None':
        category_name = Category.objects.get(id=int(selected_category_id)).name
        title += f" in {category_name} Category"

    elements.append(Paragraph(title, styles['Title']))

    data = [['Title', 'Category', 'Sold Price', 'Buyer', 'Seller', 'End Time']]
    for item in items:
        end_time_formatted = item.end_time.strftime('%B %d, %Y %I:%M %p')
        data.append([
            item.title,
            item.category.name,
            f"${item.sold_price}",
            item.buyer.get_full_name(),
            item.user.get_full_name(),
            end_time_formatted
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.aliceblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    response.write(buffer.getvalue())
    buffer.close()
    return response
@user_passes_test(is_admin)
def report_user_table(request):
    users = User.objects.all()
    return render(request, 'auction/report_user_table.html', {'users': users})
from io import BytesIO
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from .models import User

@user_passes_test(is_admin)
def download_user_table_report(request):
    users = User.objects.all()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="user_table_report.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph("User Table Report", styles['Title']))

    data = [['Username', 'Real Name', 'Email', 'Shipping Address']]
    for user in users:
        data.append([
            user.username,
            user.get_full_name(),
            user.email,
            user.shipping_address
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.aliceblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response