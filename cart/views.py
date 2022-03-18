import datetime
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from cart.models import (
    Address,
    Category,
    Order,
    OrderItem,
    Payment,
    Product,
    StripePayment,
)
from .utils import get_or_set_order_session
from .forms import AddToCartForm, AddressForm


from django.contrib import messages


from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q

import stripe

stripe.api_key = "sk_test_51JuBBUBQiGyA5MbMg18MgW2S3r5Cmnie1B8gPp5sMBcPySHEIVTwx4LeTeKHEz9FHAKrT7wLWaU6zWeZQJq1dAy200d52eeXkb"

from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone


class ProductListView(generic.ListView):
    template_name = "cart/product_list.html"

    def get_queryset(self):
        qs = Product.objects.all()

        category = self.request.GET.get("category", None)

        if category:
            qs = qs.filter(
                Q(primary_category__name=category)
                | Q(secondary_categories__name=category)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super(ProductListView, self).get_context_data(**kwargs)
        context.update(
            {
                "categories": Category.objects.values_list("name", flat=True),
            }
        )
        return context


class ProductDetailView(generic.FormView):
    template_name = "cart/product_detail.html"
    form_class = AddToCartForm

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get_success_url(self):
        return reverse("cart:cart")  # to checkout

    def get_form_kwargs(self):
        kwargs = super(ProductDetailView, self).get_form_kwargs()
        kwargs["product_id"] = self.get_object().id
        return kwargs

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        product = self.get_object()

        item_filter = order.items.filter(
            product=product,
            color=form.cleaned_data["color"],
            size=form.cleaned_data["size"],
        )

        if item_filter.exists():
            item = item_filter.first()
            item.quantity += int(form.cleaned_data["quantity"])
            item.save()

        else:
            new_item = form.save(commit=False)
            new_item.product = product
            new_item.order = order
            new_item.save()

        return super(ProductDetailView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context.update(
            {
                "product": self.get_object(),
            }
        )
        return context


class CartView(generic.TemplateView):
    template_name = "cart/cart.html"

    def get_context_data(self, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)
        context.update(
            {
                "order": get_or_set_order_session(self.request),
            }
        )
        return context


class IncreaseQuantityView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs["pk"])
        order_item.quantity += 1
        order_item.save()
        return redirect("cart:cart")


class DecreaseQuantityView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs["pk"])
        if order_item.quantity <= 1:
            order_item.delete()
        else:
            order_item.quantity -= 1
            order_item.save()
        return redirect("cart:cart")


class RemoveFromCartView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item = get_object_or_404(OrderItem, id=kwargs["pk"])
        order_item.delete()
        return redirect("cart:cart")


class CheckoutView(LoginRequiredMixin, generic.FormView):
    template_name = "cart/checkout.html"
    form_class = AddressForm

    def get_success_url(self):
        return reverse("cart:payment")

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)

        selected_shipping_address = form.cleaned_data.get("selected_shipping_address")
        selected_billing_address = form.cleaned_data.get("selected_billing_address")

        ####################################################
        if selected_shipping_address:
            order.shipping_address = selected_shipping_address

        else:
            address = Address.objects.create(
                address_type="S",
                user=self.request.user,
                name=form.cleaned_data["sname"],
                zip_code=form.cleaned_data["shipping_zip_code"],
                adress=form.cleaned_data["sadress"],
            )
            order.shipping_address = address
        ####################################################

        if selected_billing_address:
            order.billing_address = selected_billing_address

        else:
            address = Address.objects.create(
                address_type="B",
                user=self.request.user,
                name=form.cleaned_data["bname"],
                zip_code=form.cleaned_data["billing_zip_code"],
                adress=form.cleaned_data["badress"],
            )
            order.billing_address = address
            ####################################################

        order.save()
        messages.info(self.request, "success added your addresses")
        return super(CheckoutView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(CheckoutView, self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        return context

    def get_form_kwargs(self):
        kwargs = super(CheckoutView, self).get_form_kwargs()
        kwargs["user_id"] = self.request.user.id
        return kwargs


class PaymentView(generic.TemplateView):
    template_name = "cart/payment.html"

    def get_context_data(self, **kwargs):
        context = super(PaymentView, self).get_context_data(**kwargs)
        context["PAYPAL_CLIENT_ID"] = settings.PAYPAL_CLIENT_ID
        context["order"] = get_or_set_order_session(self.request)
        context["URL"] = self.request.build_absolute_uri(reverse("cart:thanks"))
        return context


class ThankYouView(generic.TemplateView):
    template_name = "cart/thanks.html"


class ConfirmOrderView(generic.View):
    def post(self, request, *args, **kwargs):
        body = json.loads(request.body)
        print(body)

        order = get_or_set_order_session(request)
        payment = Payment.objects.create(
            order=order,
            successful=True,
            response=json.dumps(body),
            amount=int(body["purchase_units"][0]["amount"]["value"]),
            payment_method="PayPal",
        )

        order.ordered = True
        order.ordered_date = datetime.date.today()
        order.save()

        return JsonResponse({"data": "Success"})


class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = "order_detail.html"
    queryset = Order.objects.all()
    context_object_name = "order"


class StripePaymentView(generic.TemplateView):
    template_name = "cart/stripe_payment.html"

    def get_context_data(self, **kwargs):
        context = super(StripePaymentView, self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)

        return context


class CreateCheckoutSessionView(LoginRequiredMixin, generic.View):
    def post(self, request, *args, **kwargs):
        order = get_or_set_order_session(self.request)
        user = self.request.user

        if not user.stripe_customer_id:
            stripe_customer = stripe.Customer.create(email=user.email)
            user.stripe_customer_id = stripe_customer["id"]
            user.save()
        ####################################################

        if order.items.all().count() == 0 or order.shipping_address == None:
            messages.error(self.request, "empty cart or no address")
            return redirect("home")

        ####################################################

        domain = "https://domain.com"
        if settings.DEBUG:
            domain = "http://127.0.0.1:8000"

        ####################################################

        customer = request.user.stripe_customer_id

        ####################################################

        line_items = []

        for item in order.items.all():
            # product_image_url = domain + item.product.image.url
            product_image_url = (
                "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg"
            )
            name = f"{item.product.title} x {item.quantity}, {item.color}, {item.size}"

            line_item = {
                "price_data": {
                    "currency": "jpy",
                    "product_data": {
                        "name": name,
                        "images": [product_image_url],
                    },
                    "unit_amount": item.product.price,
                },
                "quantity": item.quantity,
            }
            line_items.append(line_item)

        ####################################################

        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer,
                line_items=line_items,
                mode="payment",
                success_url=domain + reverse("cart:thanks"),
                cancel_url=domain + reverse("cart:product-list"),
                metadata={
                    "order_id": order.pk,
                },
            )
        except Exception as e:
            return str(e)

        return redirect(checkout_session.url, code=303)


@csrf_exempt
def stripe_webhook(request, *args, **kwargs):
    event = None
    payload = request.body
    sig_header = request.headers["STRIPE_SIGNATURE"]
    endpoint_secret = "whsec_q7KPupyswGU1zfuoaia7j6eMKiUl0ORR"

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)

    except ValueError as e:
        # Invalid payload
        print(e)
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(e)
        return HttpResponse(status=400)

    # Handle the event
    if event["type"] == "checkout.session.completed":
        event = event["data"]["object"]

        order = Order.objects.get(pk=int(event["metadata"]["order_id"]))

        stripe_payment = StripePayment.objects.create(
            order=order,
            payment_method="Stripe",
            successful=True,
            amount=event["amount_total"],
            response=event,
        )

        order = stripe_payment.order
        order.ordered = True
        order.ordered_date = timezone.now()
        order.save()

    else:
        print("Unhandled event type {}".format(event["type"]))

    return HttpResponse()
