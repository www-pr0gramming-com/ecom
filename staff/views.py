from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from cart.models import Order

from .mixins import StaffUserMixin


class StaffView(LoginRequiredMixin, StaffUserMixin, generic.ListView):
    template_name = "staff/staff.html"
    queryset = Order.objects.filter(ordered=False).order_by("-ordered_date")
    paginate_by = 1
    context_object_name = "orders"
