# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.http import JsonResponse, HttpResponse
from django.db import models
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .shopify_connector import ShopifyConnector
from .data_processing import process_customer_data
from .segmentation import segment_customers
from .analytics import plot_segments
from .models import Customer, Segment, Store, SegmentMembership, Waitlist
from .forms import StoreForm, SegmentForm, UserRegistrationForm
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json


def index(request):
    waitlist = Waitlist()
    if request.method == 'POST':
        email = request.data.get('email')
        name = request.data.get('name')

        waitlist.email = email
        waitlist.name = name
        waitlist.save()

    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})


def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                return HttpResponse("Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def logout(request):
    auth_logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    stores = Store.objects.filter(user=request.user)
    segments = Segment.objects.filter(store__user=request.user)
    recent_interactions = Customer.objects.filter(store__user=request.user).order_by('-created_at')[:10]
    segment_distribution = Segment.objects.filter(store__user=request.user).annotate(
        customer_count=models.Count('customers'))
    return render(request, 'dashboard.html', {
        'stores': stores,
        'segments': segments,
        'recent_interactions': recent_interactions,
        'segment_distribution': segment_distribution
    })


@login_required
def choose_store_method(request):
    return render(request, 'choose_store_method.html')


@login_required
def add_store(request):
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save(commit=False)
            store.user = request.user
            store.is_active = False
            store.save()
            request.session['store_id'] = store.id
            return redirect('store_payment', store_id=store.id)
    else:
        form = StoreForm()
    return render(request, 'add_store.html', {'form': form})


@login_required
def store_payment(request, store_id):
    store = Store.objects.get(id=store_id)
    if store.user != request.user:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.user.email
        kobo = 1000
        amount = 50000 * kobo  # Amount in kobo (5000 kobo = 50 NGN)

        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }

        data = {
            'email': email,
            'amount': amount,
            'callback_url': settings.PAYSTACK_CALLBACK_URL,
        }

        response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            return redirect(response_data['data']['authorization_url'])
        else:
            return render(request, 'store_payment.html', {'store': store, 'error': response.text})

    return render(request, 'store_payment.html', {'store': store})


@login_required
def shopify_auth(request):
    shop = request.GET.get('shop')
    if not shop:
        return HttpResponse("No shop parameter provided")

    shopify_oauth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={settings.SHOPIFY_API_KEY}&"
        f"scope={settings.SHOPIFY_SCOPES}&"
        f"redirect_uri={urllib.parse.quote(settings.SHOPIFY_REDIRECT_URI)}"
    )
    return redirect(shopify_oauth_url)


@login_required
def shopify_callback(request):
    code = request.GET.get('code')
    shop = request.GET.get('shop')

    if not code or not shop:
        return HttpResponse("No code or shop parameter provided")

    # Exchange the code for an access token
    token_request_data = {
        'client_id': settings.SHOPIFY_API_KEY,
        'client_secret': settings.SHOPIFY_API_SECRET,
        'code': code
    }
    response = requests.post(f"https://{shop}/admin/oauth/access_token", data=token_request_data)
    response_data = response.json()
    access_token = response_data.get('access_token')

    if not access_token:
        return HttpResponse("Failed to retrieve access token")

    # Save the store details and access token in the database
    store, created = Store.objects.update_or_create(
        user=request.user,
        store_domain=shop,
        defaults={'access_token': access_token, 'is_active': True}
    )

    return redirect('dashboard')


@login_required
def get_customers(request, store_id):
    store = Store.objects.get(id=store_id)
    if store.user != request.user or not store.is_active:
        return redirect('dashboard')

    shopify_connector = ShopifyConnector(store)
    customers = shopify_connector.get_customers()
    customer_df = process_customer_data(customers)

    # Clear existing data for this store
    Customer.objects.filter(store=store).delete()

    # Save customers to the database
    customer_instances = []
    for _, row in customer_df.iterrows():
        customer = Customer(
            store=store,
            shopify_id=row['id'],
            email=row['email'],
            created_at=row['created_at'],
            total_spent=row['total_spent'],
            orders_count=row['orders_count'],
            last_order_id=row['last_order_id']
        )
        customer_instances.append(customer)
    Customer.objects.bulk_create(customer_instances)

    # Segment customers
    segmented_customers = segment_customers(customer_df, 4)

    # Save segments to the database
    SegmentMembership.objects.filter(customer__store=store).delete()
    for _, row in segmented_customers.iterrows():
        customer = Customer.objects.get(shopify_id=row['id'], store=store)
        segment, created = Segment.objects.get_or_create(
            store=store,
            name=row['segment']
        )
        SegmentMembership.objects.create(segment=segment, customer=customer)

    # Create response with customer details and segments
    response_data = []
    for _, row in segmented_customers.iterrows():
        response_data.append({
            'id': row['id'],
            'email': row['email'],
            'created_at': row['created_at'],
            'total_spent': row['total_spent'],
            'orders_count': row['orders_count'],
            'segment': row['segment']
        })

    plot_segments(segmented_customers)
    return JsonResponse(response_data, safe=False)


@login_required
@csrf_exempt
def webhook(request):
    data = json.loads(request.body)
    user_email = data['user_email']
    user = User.objects.get(email=user_email)
    store = Store.objects.get(user=user)

    for customer_data in data['customers']:
        customer, created = Customer.objects.update_or_create(
            store=store,
            shopify_id=customer_data['id'],
            defaults={
                'email': customer_data['email'],
                'created_at': customer_data['created_at'],
                'total_spent': customer_data['total_spent'],
                'orders_count': customer_data['orders_count'],
                'last_order_id': customer_data['last_order_id'],
            }
        )

    customers = Customer.objects.filter(store=store)
    customer_df = pd.DataFrame(list(customers.values()))
    segmented_customers = segment_customers(customer_df, 4)

    SegmentMembership.objects.filter(customer__store=store).delete()
    for _, row in segmented_customers.iterrows():
        customer = Customer.objects.get(shopify_id=row['id'], store=store)
        segment, created = Segment.objects.get_or_create(
            store=store,
            name=row['segment']
        )
        SegmentMembership.objects.create(segment=segment, customer=customer)

    return HttpResponse(status=200)


@login_required
def add_segment(request):
    if request.method == 'POST':
        form = SegmentForm(request.POST)
        if form.is_valid():
            segment = form.save(commit=False)
            segment.store = Store.objects.get(user=request.user)
            segment.save()
            return redirect('dashboard')
    else:
        form = SegmentForm()
    return render(request, 'add_segment.html', {'form': form})
