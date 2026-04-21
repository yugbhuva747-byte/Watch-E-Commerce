from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Watch, Cart, Order, OrderItem, ContactMessage, Review, User


# ───────────── PUBLIC PAGES ─────────────

def homepage(request):
    featured = Watch.objects.filter(is_active=True, is_featured=True)[:6]
    all_watches = Watch.objects.filter(is_active=True)[:6]
    context = {
        'featured': featured if featured.exists() else all_watches,
        'total_watches': Watch.objects.filter(is_active=True).count(),
    }
    return render(request, 'home.html', context)


def productpage(request):
    category = request.GET.get('category', '')
    search = request.GET.get('q', '')
    sort = request.GET.get('sort', 'created_at')
    watches = Watch.objects.filter(is_active=True)
    if category:
        watches = watches.filter(category=category)
    if search:
        watches = watches.filter(Q(name__icontains=search) | Q(brand__icontains=search))
    sort_map = {
        'price_asc': 'price', 'price_desc': '-price',
        'name': 'name', 'created_at': '-created_at',
    }
    watches = watches.order_by(sort_map.get(sort, '-created_at'))
    context = {
        'watches': watches,
        'category': category,
        'search': search,
        'sort': sort,
        'total': watches.count(),
    }
    return render(request, 'product.html', context)


def watch_detail(request, pk):
    watch = get_object_or_404(Watch, pk=pk, is_active=True)
    watch.views_count += 1
    watch.save(update_fields=['views_count'])
    reviews = watch.reviews.all().order_by('-created_at')
    related = Watch.objects.filter(category=watch.category, is_active=True).exclude(pk=pk)[:4]
    context = {'watch': watch, 'reviews': reviews, 'related': related}
    return render(request, 'watch_detail.html', context)


def aboutpage(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        ContactMessage.objects.create(
            name=request.POST.get('name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            subject=request.POST.get('subject', ''),
            message=request.POST.get('message', ''),
        )
        messages.success(request, 'Your message has been sent!')
        return redirect('contact')
    return render(request, 'contact.html')


# ───────────── AUTH ─────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        user = authenticate(
            username=request.POST.get('username', ''),
            password=request.POST.get('password', ''),
        )
        if user:
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'seller':
                return redirect('seller_dashboard')
            return redirect('homepage')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'buyer')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password, role=role)
            login(request, user)
            return redirect('homepage')
    return render(request, 'register.html')


def logout_view(request):
    logout(request)
    return redirect('homepage')


# ───────────── CART ─────────────

@login_required
def cart_view(request):
    items = Cart.objects.filter(user=request.user).select_related('watch')
    total = sum(item.subtotal for item in items)
    return render(request, 'cart.html', {'items': items, 'total': total})


@login_required
def add_to_cart(request, pk):
    watch = get_object_or_404(Watch, pk=pk)
    item, created = Cart.objects.get_or_create(user=request.user, watch=watch)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f'"{watch.name}" added to cart.')
    return redirect('cart')


@login_required
def remove_from_cart(request, pk):
    Cart.objects.filter(user=request.user, watch_id=pk).delete()
    return redirect('cart')


@login_required
def checkout(request):
    items = Cart.objects.filter(user=request.user).select_related('watch')
    if not items.exists():
        return redirect('cart')
    total = sum(i.subtotal for i in items)
    if request.method == 'POST':
        order = Order.objects.create(user=request.user, total_price=total,
                                     shipping_address=request.POST.get('address', ''))
        for item in items:
            OrderItem.objects.create(order=order, watch=item.watch,
                                     quantity=item.quantity, price=item.watch.price)
            w = item.watch
            w.stock = max(0, w.stock - item.quantity)
            w.save(update_fields=['stock'])
        items.delete()
        messages.success(request, f'Order #{order.id} placed successfully!')
        return redirect('order_success')
    return render(request, 'checkout.html', {'items': items, 'total': total})


def order_success(request):
    return render(request, 'order_success.html')


# ───────────── SELLER DASHBOARD ─────────────

@login_required
def seller_dashboard(request):
    if request.user.role not in ('seller', 'admin'):
        return redirect('homepage')
    watches = Watch.objects.filter(seller=request.user)
    orders = Order.objects.filter(items__watch__seller=request.user).distinct().order_by('-created_at')
    revenue = orders.filter(status='delivered').aggregate(total=Sum('total_price'))['total'] or 0
    context = {
        'watches': watches,
        'orders': orders[:10],
        'total_watches': watches.count(),
        'total_orders': orders.count(),
        'revenue': revenue,
        'low_stock': watches.filter(stock__lte=3),
    }
    return render(request, 'seller_dashboard.html', context)


@login_required
def add_watch(request):
    if request.user.role not in ('seller', 'admin'):
        return redirect('homepage')
    if request.method == 'POST':
        Watch.objects.create(
            seller=request.user,
            name=request.POST['name'],
            brand=request.POST['brand'],
            price=request.POST['price'],
            description=request.POST['description'],
            image=request.FILES.get('image'),
            stock=request.POST['stock'],
            category=request.POST.get('category', 'classic'),
            material=request.POST.get('material', ''),
            movement=request.POST.get('movement', ''),
            is_featured=request.POST.get('is_featured') == 'on',
        )
        messages.success(request, 'Watch listed successfully!')
        return redirect('seller_dashboard')
    return render(request, 'add_watch.html')


@login_required
def edit_watch(request, pk):
    watch = get_object_or_404(Watch, pk=pk, seller=request.user)
    if request.method == 'POST':
        watch.name = request.POST['name']
        watch.brand = request.POST['brand']
        watch.price = request.POST['price']
        watch.description = request.POST['description']
        watch.stock = request.POST['stock']
        watch.category = request.POST.get('category', watch.category)
        watch.material = request.POST.get('material', watch.material)
        watch.movement = request.POST.get('movement', watch.movement)
        watch.is_featured = request.POST.get('is_featured') == 'on'
        if request.FILES.get('image'):
            watch.image = request.FILES['image']
        watch.save()
        messages.success(request, 'Watch updated.')
        return redirect('seller_dashboard')
    return render(request, 'edit_watch.html', {'watch': watch})


@login_required
def delete_watch(request, pk):
    watch = get_object_or_404(Watch, pk=pk, seller=request.user)
    watch.delete()
    messages.success(request, 'Watch removed.')
    return redirect('seller_dashboard')


# ───────────── ADMIN PANELS ─────────────

def _admin_required(request):
    return request.user.is_authenticated and request.user.role == 'admin'


def admin_dashboard(request):
    if not _admin_required(request):
        return redirect('login')
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    context = {
        'total_users': User.objects.count(),
        'total_watches': Watch.objects.count(),
        'total_orders': Order.objects.count(),
        'total_revenue': Order.objects.filter(status='delivered').aggregate(t=Sum('total_price'))['t'] or 0,
        'recent_orders': Order.objects.order_by('-created_at')[:8],
        'recent_users': User.objects.order_by('-date_joined')[:6],
        'month_orders': Order.objects.filter(created_at__gte=month_start).count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'messages_unread': ContactMessage.objects.filter(is_read=False).count(),
        'low_stock_watches': Watch.objects.filter(stock__lte=3, is_active=True),
        'sellers': User.objects.filter(role='seller'),
    }
    context.update(_admin_ctx()); return render(request, 'admin_dashboard.html', context)


def admin_users(request):
    if not _admin_required(request):
        return redirect('login')
    role_filter = request.GET.get('role', '')
    users = User.objects.all().order_by('-date_joined')
    if role_filter:
        users = users.filter(role=role_filter)
    search = request.GET.get('q', '')
    if search:
        users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))
    return render(request, 'admin_users.html', _admin_ctx({'users': users, 'role_filter': role_filter, 'search': search}))


def admin_toggle_user(request, pk):
    if not _admin_required(request):
        return redirect('login')
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return redirect('admin_users')


def admin_orders(request):
    if not _admin_required(request):
        return redirect('login')
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all().select_related('user').order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'admin_orders.html', _admin_ctx({'orders': orders, 'status_filter': status_filter}))


def admin_update_order(request, pk):
    if not _admin_required(request):
        return redirect('login')
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.status = request.POST.get('status', order.status)
        order.save(update_fields=['status'])
    return redirect('admin_orders')


def admin_watches(request):
    if not _admin_required(request):
        return redirect('login')
    watches = Watch.objects.all().select_related('seller').order_by('-created_at')
    return render(request, 'admin_watches.html', _admin_ctx({'watches': watches}))


def admin_messages(request):
    if not _admin_required(request):
        return redirect('login')
    msgs = ContactMessage.objects.all().order_by('-created_at')
    ContactMessage.objects.filter(is_read=False).update(is_read=True)
    return render(request, 'admin_messages.html', _admin_ctx({'messages': msgs}))


# ───────────── SELLER PANEL (role-based) ─────────────

def seller_orders(request):
    if not (request.user.is_authenticated and request.user.role in ('seller', 'admin')):
        return redirect('login')
    orders = Order.objects.filter(items__watch__seller=request.user).distinct().order_by('-created_at')
    return render(request, 'seller_orders.html', {'orders': orders})


# ───────────── API ─────────────

@api_view(['GET'])
def watch_api(request):
    category = request.GET.get('category', '')
    watches = Watch.objects.filter(is_active=True)
    if category:
        watches = watches.filter(category=category)
    data = []
    for w in watches:
        data.append({
            'id': w.id,
            'name': w.name,
            'brand': w.brand,
            'price': w.price,
            'description': w.description,
            'image': request.build_absolute_uri(w.image.url) if w.image else '',
            'stock': w.stock,
            'category': w.category,
            'material': w.material,
            'movement': w.movement,
            'is_featured': w.is_featured,
            'created_at': str(w.created_at),
        })
    return Response(data)


@api_view(['GET'])
def stats_api(request):
    return Response({
        'total_watches': Watch.objects.filter(is_active=True).count(),
        'total_orders': Order.objects.count(),
        'total_revenue': Order.objects.filter(status='delivered').aggregate(t=Sum('total_price'))['t'] or 0,
        'total_users': User.objects.count(),
    })


# Context helper — inject unread count into admin templates
def _admin_ctx(base=None):
    ctx = base or {}
    ctx['unread_count'] = ContactMessage.objects.filter(is_read=False).count()
    return ctx
