from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'panel'

urlpatterns = [
    path('', views.index, name='index'),
    path('panelsprzedawcy/', views.seller_panel, name='Panel sprzedawcy'),
    path('panelsprzedawcy/programkasowy/', views.cash_register, name='Program kasowy'),
    path('panelsprzedawcy/programkasowy/<int:id>/', views.transaction_summary, name='Podsumowanie transakcji'),
    path('panelsprzedawcy/magazyn/', views.warehouse, name='Magazyn'),
    path('panelsprzedawcy/sprzedaz/', views.sale_seller, name='Sprzedaż'),
    path('panelsprzedawcy/ksk/', views.ksk, name='Karta stałego klienta'),
    path('panelcentralny/', views.central_panel, name='Panel centralny'),
    path('panelcentralny/obroty/', views.sales, name='Obroty'),
    path('panelcentralny/stok/', views.stock, name='Stok'),
    path('panelcentralny/stok/<int:pk>/', views.product_view, name='Widok produktu'),
    path('panelcentralny/zarzadzanie/', views.management, name='Zarządzanie'),
    path('panelcentralny/zarzadzanie/zmianacen/', views.price_changes_stand_choice, name='Wybór stoiska zmiany cen'),
    path('panelcentralny/zarzadzanie/zmianacen/<owner>/', views.price_changes_plu_choice, name='Wybór plu zmiany cen'),
    path('panelcentralny/zarzadzanie/zmianacen/<owner>/<int:plu>/', views.price_changes, name='Zmiana ceny'),
    path('panelcentralny/zarzadzanie/zamowienia/', views.orders_stand_choice, name='Wybór stoiska zamówienia'),
    path('panelcentralny/zarzadzanie/zamowienia/<owner>/', views.orders_plu_choice, name='Wybór plu zamówienia'),
    path('panelcentralny/zarzadzanie/zamowienia/<owner>/<int:plu>/', views.orders, name='Zamówienia'),
    path('panelcentralny/wyniki/', views.sales_records, name='Wyniki'),
    path('panelcentralny/kontakt/', views.contact, name='Kontakt'),
    path('panelcentralny/kartysk/', views.ksk_view, name='Kartysk'),
    path('panelcentralny/kartysk/(\d+)/', views.ksk_view_details, name='kskdetails'),
    path('panelcentralny/stoiska/', views.stands, name='Stoiska'),
    path('panelcentralny/stoiska/tworzeniestoiska/', views.stand_creation, name='Tworzenie stoiska')
]
