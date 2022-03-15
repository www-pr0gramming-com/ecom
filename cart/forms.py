from django import forms
from .models import Address, ColorVariation, OrderItem, Product, SizeVariation
from django.contrib.auth import get_user_model

User = get_user_model()


class AddToCartForm(forms.ModelForm):
    color = forms.ModelChoiceField(queryset=ColorVariation.objects.none())
    size = forms.ModelChoiceField(queryset=SizeVariation.objects.none())

    class Meta:
        model = OrderItem
        fields = ["quantity", "color", "size"]

    def __init__(self, *args, **kwargs):
        product_id = kwargs.pop("product_id")
        product = Product.objects.get(id=product_id)
        super().__init__(*args, **kwargs)

        self.fields["color"].queryset = product.available_colors.all()
        self.fields["size"].queryset = product.available_sizes.all()


class AddressForm(forms.Form):

    sname = forms.CharField(required=False)
    shipping_zip_code = forms.CharField(required=False)
    sadress = forms.CharField(required=False)

    ###################################
    bname = forms.CharField(required=False)
    billing_zip_code = forms.CharField(required=False)
    badress = forms.CharField(required=False)

    ###################################

    selected_shipping_address = forms.ModelChoiceField(
        Address.objects.none(), required=False
    )

    selected_billing_address = forms.ModelChoiceField(
        Address.objects.none(), required=False
    )

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop("user_id")
        super().__init__(*args, **kwargs)
        user = User.objects.get(id=user_id)

        shipping_address_qs = Address.objects.filter(user=user, address_type="S")
        billing_address_qs = Address.objects.filter(user=user, address_type="B")

        self.fields["selected_shipping_address"].queryset = shipping_address_qs
        self.fields["selected_billing_address"].queryset = billing_address_qs

    def clean(self):
        selected_shipping_address = self.cleaned_data.get(
            "selected_shipping_address", None
        )

        if selected_shipping_address is None:
            if not self.cleaned_data.get("sname", None):
                self.add_error("sname", "empty")
            if not self.cleaned_data.get("shipping_zip_code", None):
                self.add_error("shipping_zip_code", "empty")
            if not self.cleaned_data.get("sadress", None):
                self.add_error("sadress", "empty")

        ##########################################################
        selected_billing_address = self.cleaned_data.get(
            "selected_billing_address", None
        )

        if selected_billing_address is None:
            if not self.cleaned_data.get("bname", None):
                self.add_error("bname", "empty")
            if not self.cleaned_data.get("billing_zip_code", None):
                self.add_error("billing_zip_code", "empty")
            if not self.cleaned_data.get("badress", None):
                self.add_error("badress", "empty")

        ##########################################################
