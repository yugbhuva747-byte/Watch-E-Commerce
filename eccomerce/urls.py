from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from Eapp import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public
    path('', views.homepage, name='homepage'),
    path('products/', views.productpage, name='productpage'),
    path('products/<int:pk>/', views.watch_detail, name='watch_detail'),
    path('about/', views.aboutpage, name='aboutpage'),
    path('contact/', views.contact, name='contact'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Cart & Orders
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/', views.order_success, name='order_success'),

    # Seller Panel
    path('seller/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/orders/', views.seller_orders, name='seller_orders'),
    path('seller/add/', views.add_watch, name='add_watch'),
    path('seller/edit/<int:pk>/', views.edit_watch, name='edit_watch'),
    path('seller/delete/<int:pk>/', views.delete_watch, name='delete_watch'),

    # Admin Panels
    path('panel/', views.admin_dashboard, name='admin_dashboard'),
    path('panel/users/', views.admin_users, name='admin_users'),
    path('panel/users/toggle/<int:pk>/', views.admin_toggle_user, name='admin_toggle_user'),
    path('panel/orders/', views.admin_orders, name='admin_orders'),
    path('panel/orders/update/<int:pk>/', views.admin_update_order, name='admin_update_order'),
    path('panel/watches/', views.admin_watches, name='admin_watches'),
    path('panel/messages/', views.admin_messages, name='admin_messages'),

    # API
    path('api/watches/', views.watch_api, name='watch_api'),
    path('api/stats/', views.stats_api, name='stats_api'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
