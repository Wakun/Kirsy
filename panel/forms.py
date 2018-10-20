from django import forms
from django.forms import DateField
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.utils import timezone

from .models import Product, Ksk, Stand

class CustomModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s" % obj.owner_name


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ('plu_num', 'art_name', "sales_price_brutto")


class KskForm(forms.ModelForm):

    class Meta:
        model = Ksk
        fields = ('card_number', 'name', 'surname', 'street', 'apartement_number', 'building_number', 'city',
                  'postal_code', 'email', 'phone_number')


class StandForm(forms.ModelForm):

    class Meta:
        model = Stand
        fields = ('stand_name', 'adress')


class StandCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')


class TransactionForm(forms.Form):

    is_paid = forms.BooleanField(label='is_paid')


class SalesDateForm(forms.Form):

    date = DateField(widget=forms.SelectDateWidget(), label='Wybierz datę', initial=timezone.now())


class PriceChangesChoice(forms.Form):

    plu_num = forms.IntegerField(label='PLU')
    owner = forms.ModelChoiceField(queryset=Group.objects.all())

class PriceAndPromoForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ('sales_price_brutto',)
