from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Product, Stand, Ksk, Transaction


class ProductAdmin(SimpleHistoryAdmin):

    fieldsets = [
        (None, {'fields': ['art_name']}),
        ('PLU', {'fields': ['plu_num']}),
        ('Ceny zakupu i sprzedaży', {'fields': ['purchase_price_brutto', 'sales_price_brutto', 'vat_value']}),
        ('Stan', {'fields': ['stock']}),
        ('Data wejścia', {'fields': ['entry_date']}),
        ('Grupa', {'fields': ['owner']}),
    ]

    history_list_display = ['sales_price_netto', 'sales_price_brutto', 'stock', 'quantity_sold', 'temporary_quantity']

    list_display = ('plu_num', 'art_name', 'purchase_price_netto', 'purchase_price_brutto', 'sales_price_netto',
                    'sales_price_brutto', 'margin', 'zloty_margin', 'last_price', 'vat_value', 'vat_difference',
                    'stock', 'stock_cz_pln', 'stock_cs_pln', 'decote', 'entry_date', 'owner', 'quantity_sold', 'temporary_quantity')

    list_filter = ['owner']

    search_fields = ['art_name', 'plu_num']




class StandAdmin(admin.ModelAdmin):

    fieldsets = [
        ('Nazwa stoiska', {'fields': ['stand_name']}),
        ('Adres stoiska', {'fields': ['adress']}),
    ]

    list_display = ('stand_name', 'adress')


class KskAdmin(admin.ModelAdmin):

    fieldsets = [
        (None, {'fields': ['card_number']}),
        ('Imię i nazwisko', {'fields': ['name', 'surname']}),
        ('Adres', {'fields': ['street', 'apartement_number', 'building_number', 'city', 'postal_code']}),
        ('Dane kontaktowe', {'fields': ['phone_number', 'email']})
    ]

    list_display = ('card_number', 'full_name', 'adress', 'city', 'postal', 'email', 'phone_number', 'purchase_value', 'points')

    list_filter = ['card_number', 'city', 'purchase_value']

    search_fields = ['city', 'card_number', 'postal']


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'plu_list', 'transaction_date', 'is_ksk', 'ksk_num', 'is_paid', 'total', 'owner')




admin.site.register(Product, ProductAdmin)
admin.site.register(Stand, StandAdmin)
admin.site.register(Ksk, KskAdmin)
admin.site.register(Transaction, TransactionAdmin)


