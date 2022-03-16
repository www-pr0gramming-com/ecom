from django.contrib import admin
from .models import (
    Address,
    Product,
    OrderItem,
    Order,
    ColorVariation,
    SizeVariation,
    Payment,
)


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "name",
        "adress",
        "zip_code",
        "address_type",
    ]


admin.site.register(Product)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(ColorVariation)
admin.site.register(SizeVariation)
admin.site.register(Address, AddressAdmin)
admin.site.register(Payment)
