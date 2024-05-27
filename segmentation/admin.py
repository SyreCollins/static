from django.contrib import admin
from .models import Store, Customer, Segment, SegmentMembership, Waitlist

# Register your models here.
admin.site.register(Store)
admin.site.register(Customer)
admin.site.register(Segment)
admin.site.register(SegmentMembership)
admin.site.register(Waitlist)