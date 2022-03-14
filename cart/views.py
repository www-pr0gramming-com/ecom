from django.shortcuts import render
from django.views import generic

from cart.models import Product


class ProductListView(generic.ListView):
    template_name = "cart/product_list.html"
    queryset = Product.objects.all()
