from django.db import models
from django.contrib.auth.models import User, Group
from datetime import datetime
from simple_history.models import HistoricalRecords
import json




decote_dict = {'styczeń': 1, 'luty': 2, 'marzec': 3, 'kwiecień': 4, 'maj': 5, 'czerwiec': 6, 'lipiec': 7,
               'sierpień': 8, 'wrzesień': 9, 'październik': 10, 'listopad': 11, 'grudzień': 12}

vat_dict = {'23%': 1.23, '8%': 1.08, '5%': 1.05, '0%': 1.0}


def format_currency(price):
    formatted_price = u''
    if price:
        try:
            formatted_price = u'{:,.2f} zł'.format(price).replace(',', '').replace('.', ',')
        except ValueError:
            pass
    return formatted_price


def format_vat(vat):
    formatted_vat = u''
    if vat:
        try:
            formatted_vat = u'{}%'.format(vat)
        except ValueError:
            pass
    return formatted_vat


def format_zloty_margin(zl_margin):
    formatted_zloty_margin = u''
    if zl_margin:
        try:
            formatted_zloty_margin = u'{:.2f} zł'.format(zl_margin)
        except ValueError:
            pass
    return formatted_zloty_margin


class Product(models.Model):

    VAT_CHOICES = (
        ('23', 23),
        ('8', 8),
        ('5', 5),
        ('0', 0),
    )

    STATUS_CHOICES = (
        ('AC', 'AC'),
        ('NC', 'NC'),
    )

    art_name = models.CharField('Nazwa artykułu: ', max_length=100)
    plu_num = models.IntegerField('Nr. PLU', default=0)

    sales_price_brutto = models.FloatField('CSB: ', null=True)
    sales_price_netto = models.FloatField('CSN: ', null=True)
    last_price = models.FloatField('Ostatnia cena sprzedaży: ', null=True)
    purchase_price_brutto = models.FloatField('CZB: ', null=True)
    purchase_price_netto = models.FloatField('CZN: ', null=True)
    vat_difference = models.FloatField('Różnica VAT: ', null=True)
    vat_value = models.CharField(choices=VAT_CHOICES, max_length=3, default=23)
    entry_date = models.DateField('Data wejścia: ')
    margin = models.FloatField('Marża: ', null=True)
    zloty_margin = models.FloatField('Marża PLN: ', null=True)
    stock = models.IntegerField('Stan: ', default=0)
    stock_cs_pln = models.FloatField('Stok CS PLN: ', null=True)
    stock_cz_pln = models.FloatField('Stok CZ PLN: ', null=True)
    decote = models.IntegerField('Dekot: ', default=0)

    product_status = models.CharField(choices=STATUS_CHOICES, default='AC', max_length=2)

    quantity_sold = models.IntegerField('Sprzedana ilość', default=0)
    temporary_quantity = models.IntegerField('Tymczasowa ilość', default=0)
    history = HistoricalRecords()

    owner = models.ForeignKey(Group, on_delete=models.CASCADE)
    owner_name = models.CharField('Nazwa grupy: ', max_length=255)

    price_raw_variance = models.FloatField(null=True)
    price_percentage_variance = models.FloatField(default=0.0)
    price_changes = models.IntegerField(default=0)

    class Meta:

        verbose_name = 'Produkt'
        verbose_name_plural = 'Produkty'

    def __str__(self):
        return str(self.plu_num) + ' ' + self.art_name

    def save(self, *args, **kwargs):
        self.sales_price_netto = self.get_sales_price_netto()
        self.purchase_price_netto = self.get_purchase_price_netto()
        self.vat_difference = self.get_vat_difference()
        self.margin = self.get_margin_display()
        self.zloty_margin = self.get_zloty_margin_display()
        self.stock_cs_pln = self.get_stock_cs_pln_display()
        self.stock_cz_pln = self.get_stock_cz_pln_display()
        self.decote = self.get_decote_display()
        self.owner_name = self.owner.name


        super(Product, self).save(*args, **kwargs)




    """def update_price(self, price):
        if price != self.sales_price_brutto:
            self.last_price = self.sales_price_brutto
            self.sales_price_brutto = price
            if self.sales_price_brutto and self.last_price:
                self.price_raw_variance = self.sales_price_brutto - self.last_price
                if self.sales_price_brutto > 0 and self.last_price > 0:
                    if self.last_price < self.sales_price_brutto:
                        self.price_percentage_variance = self.last_price / self.sales_price_brutto
                        self.price_percentage_variance = 1.0 - self.price_percentage_variance
                    elif self.last_price > self.sales_price_brutto:
                        self.price_percentage_variance = self.sales_price_brutto / self.last_price
                        self.price_percentage_variance = self.price_percentage_variance - 1.0
                else:
                    self.price_percentage_variance = 0.0
            else:
                self.price_raw_variance = None
                self.price_percentage_variance = 0.0
            self.price_changes = self.price_changes.count()
            self.save()
            PriceHistory(product=self, price=price).save()"""

    def get_current_price_display(self):
        return format_currency(self.sales_price_brutto)

    get_current_price_display.allow_tags = True
    get_current_price_display.short_description = 'CSB: '
    csb = property(get_current_price_display)

    def get_vat_display(self):
        return format_vat(self.vat_value)

    get_vat_display.allow_tags = True
    get_vat_display.short_description = 'VAT: '
    vat_display = property(get_vat_display)

    def get_price_raw_variance_display(self):
        value = self.price_raw_variance
        if value < 0:
            value = value * -1
        return format_currency(value)
    # !!!

    def get_price_percentage_variance_display(self):
        value = self.price_percentage_variance * 100
        if value < 0:
            value = value * -1
        return u'{:.2f}%'.format(value)
    # !!!

    def get_decote_display(self):
        decote_value = 0
        actual_date = datetime.today()
        actual_month = actual_date.month
        entry_month = self.entry_date.strftime('%m')
        entry_month = int(entry_month)

        if entry_month in decote_dict:
            entry_month = decote_dict[entry_month]

        if actual_month - entry_month <= 2:
            return decote_value
        elif actual_month - entry_month > 2:
            for i in range(actual_month - entry_month):
                decote_value += 10

        return decote_value

    """get_decote_display.allow_tags = True
    get_decote_display.short_description = 'Dekot: '
    decot = property(get_decote_display)"""

    def get_sales_price_netto(self):
        value = 0.0
        if self.vat_display in vat_dict:
            value = self.sales_price_brutto / vat_dict[self.vat_display]
        else:
            pass

        value = round(value, 2)
        return value



    def get_purchase_price_netto(self):
        value = 0.0
        if self.vat_display in vat_dict:
            value = self.purchase_price_brutto / vat_dict[self.vat_display]
        else:
            pass

        value = round(value, 2)
        return value



    def get_vat_difference(self):
        purchase_vat = self.purchase_price_brutto - self.purchase_price_netto
        sales_vat = self.sales_price_brutto - self.sales_price_netto
        vat_diff = sales_vat - purchase_vat

        vat_diff = round(vat_diff, 2)
        return vat_diff



    def get_margin_display(self):
        x = self.sales_price_brutto - self.purchase_price_brutto
        y = x - float(self.vat_difference)
        percentage_margin = (y / self.sales_price_brutto) * 100

        percentage_margin = round(percentage_margin, 2)
        return percentage_margin



    def get_zloty_margin_display(self):
        x = self.sales_price_brutto - self.purchase_price_brutto
        pln_margin = x - float(self.vat_difference)

        pln_margin = round(pln_margin, 2)

        return pln_margin



    def get_stock_cs_pln_display(self):
        stock_cs = self.sales_price_brutto * self.stock

        return stock_cs




    def get_stock_cz_pln_display(self):
        stock_cz = self.purchase_price_brutto * self.stock

        return stock_cz


class PriceHistory(models.Model):
    product = models.ForeignKey(Product, related_name='price_history', on_delete=models.CASCADE)
    price = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def get_price_display(self):
        return format_currency(self.price)


class Stand(models.Model):

    stand_name = models.CharField('Nazwa stoiska: ', max_length=255)
    adress = models.CharField('Adres: ', max_length=255)

    class Meta:

        verbose_name = 'Stoisko'
        verbose_name_plural = 'Stoiska'


class Ksk(models.Model):

    card_number = models.IntegerField('Numer karty: ', unique=True)
    name = models.CharField('Imię: ', max_length=50)
    surname = models.CharField('Nazwisko: ', max_length=100)
    street = models.CharField('Ulica: ', max_length=255)
    apartement_number = models.CharField('Nr. mieszkania', max_length=5)
    building_number = models.CharField('Nr. budynku: ', max_length=5)
    city = models.CharField('Miejscowość: ', max_length=255)
    postal_code = models.CharField('Kod pocztowy: ', max_length=6)
    email = models.EmailField(max_length=254)
    phone_number = models.IntegerField('Nr. telefonu: ', null=True)
    purchase_value = models.FloatField('Wartość zakupów: ', default=0.0)
    discount = models.IntegerField('Rabat: ', null=True)
    points = models.IntegerField('Liczba punktów', default=0)

    class Meta:
        verbose_name = 'Karta stałego klienta'
        verbose_name_plural = 'Karta stałego klienta'

    def get_adress_display(self):
        a = self.apartement_number
        b = self.building_number
        s = self.street

        adress = s + ' ' + b + '/' + a

        return adress

    get_adress_display.allow_tags = True
    get_adress_display.short_description = 'Adres: '
    adress = property(get_adress_display)

    def get_postal_code_display(self):
        p = self.postal_code

        if len(p) < 6:
            p = p[:2] + '-' + p[2:]

        return p

    get_postal_code_display.allow_tags = True
    get_postal_code_display.short_description = 'Kod pocztowy: '
    postal = property(get_postal_code_display)

    def get_name_display(self):
        return self.name + ' ' + self.surname

    get_name_display.allow_tags = True
    get_name_display.short_description = 'Imię i nazwisko: '
    full_name = property(get_name_display)

    def get_discount_display(self):
        if self.discount is not None:
            return str(self.discount) + ' %'
        else:
            return 'Brak'

    get_discount_display.allow_tags = True
    get_discount_display.short_description = 'Rabat: '
    discount_value= property(get_discount_display)


class Transaction(models.Model):

    plu_list = models.CharField(max_length=255)  #  {plu : ilość, plu : ilość}
    total = models.FloatField(null=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    is_ksk = models.BooleanField(default=False)
    ksk_num = models.IntegerField(null=True)
    is_paid = models.BooleanField(default=False)
    owner = models.ForeignKey(User, editable=False, on_delete=models.CASCADE) # konto które zrobiło transakcję


    def set_plu_list(self, x):
        self.plu_list = json.dumps(x)

    def get_plu_list(self):
        return json.loads(self.plu_list)


# model obrotów