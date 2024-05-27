# models.py
from django.db import models
from django.contrib.auth.models import User

class Waitlist(models.Model):
    email = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Store(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    store_domain = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    access_token = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Customer(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    shopify_id = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    created_at = models.DateTimeField()
    total_spent = models.DecimalField(max_digits=10, decimal_places=2)
    orders_count = models.IntegerField()
    last_order_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.email

class Segment(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    criteria = models.JSONField()  # JSON field to store segmentation criteria
    customers = models.ManyToManyField(Customer, through='SegmentMembership')

    def __str__(self):
        return self.name

class SegmentMembership(models.Model):
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.customer.email} in {self.segment.name}'
