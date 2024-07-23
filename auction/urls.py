from django.contrib import admin
from django.urls import path
from .views import home, register, login_view, item_list, item_detail, submit_item, place_bid, custom_logout_view, \
    delete_item, user_items, edit_item, report_items_bought, report_items_on_sale, report_user_table, \
    download_items_bought_report, download_items_on_sale_report

admin.site.site_header = "eBay"
admin.site.site_title = "eBay"
admin.site.index_title = "Welcome to eBay Admin Portal"

urlpatterns = [
    path('admin/', admin.site.urls),  # Include the admin site URLs
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('category/<int:category_id>/', item_list, name='item_list'),
    path('item/<int:item_id>/', item_detail, name='item_detail'),
    path('submit_item/', submit_item, name='submit_item'),
    path('place_bid/<int:item_id>/', place_bid, name='place_bid'),
    path('item/<int:item_id>/delete/', delete_item, name='delete_item'),
    path('user_items/', user_items, name='user_items'),
    path('edit_item/<int:item_id>/', edit_item, name='edit_item'),
    path('report_items_bought/', report_items_bought, name='report_items_bought'),
    path('report_items_on_sale/', report_items_on_sale, name='report_items_on_sale'),
    path('report_user_table/', report_user_table, name='report_user_table'),
    path('download_items_bought_report/', download_items_bought_report, name='download_items_bought_report'),
    path('download_items_on_sale_report/', download_items_on_sale_report, name='download_items_on_sale_report'),
]
