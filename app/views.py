from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from .forms import ContactForm

from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

from django.contrib.auth.mixins import LoginRequiredMixin

from cart.models import Order


class ContactView(generic.FormView):
    form_class = ContactForm
    template_name = "contact.html"

    def get_success_url(self):
        return reverse("contact")

    def form_valid(self, form):
        messages.info(self.request, "thank you")
        name = form.cleaned_data["name"]
        email = form.cleaned_data["email"]
        message = form.cleaned_data["message"]

        full_message = f"""
        Received from {name}, {email}
        ------------------

        {message}
        """

        send_mail(
            subject="email",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.NOTIFY_EMAIL],
        )

        return super(ContactView, self).form_valid(form)


class ProfileView(LoginRequiredMixin, generic.TemplateView):
    template_name = "profile.html"

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context.update(
            {"orders": Order.objects.filter(user=self.request.user, ordered=True)}
        )
        return context
