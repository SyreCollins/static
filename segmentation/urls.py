# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('choose_store_method/', views.choose_store_method, name='choose_store_method'),
    path('add_store/', views.add_store, name='add_store'),
    path('store_payment/<int:store_id>/', views.store_payment, name='store_payment'),
    path('shopify_auth/', views.shopify_auth, name='shopify_auth'),
    path('shopify_callback/', views.shopify_callback, name='shopify_callback'),
    path('get_customers/<int:store_id>/', views.get_customers, name='get_customers'),
    path('add_segment/', views.add_segment, name='add_segment'),
    path('webhook/', views.webhook, name='webhook'),
]
