from django.test import TestCase
from django.urls import resolve
# from django.http import HttpRequest
# from datetime import datetime

from .views import index
from .models import Product


class ProductModelTests(TestCase):

    def test_string_representation(self):
        test_product = Product(art_name='test', plu_num=123)
        self.assertEqual(str(test_product), str(test_product.plu_num) + ' ' + test_product.art_name)

    def test_get_stock_cs_pln_display(self):
        test_product = Product(art_name='test', plu_num=123, sales_price_brutto=100, stock=10)
        self.assertEqual(test_product.get_stock_cs_pln_display(), 1000)

    def test_get_stock_cz_pln_display(self):
        test_product = Product(art_name='test', plu_num=123, purchase_price_brutto=100, stock=10)
        self.assertEqual(test_product.get_stock_cz_pln_display(), 1000)


class KskModelTests(TestCase):
    pass


class PagesTests(TestCase):

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_panel_root_url_resolves_to_index(self):
        found = resolve('/kirsy/')
        self.assertEqual(found.func, index)
