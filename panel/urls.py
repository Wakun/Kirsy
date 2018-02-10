from django.conf.urls import url

from . import views

app_name = 'panel'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^panelsprzedawcy/$', views.seller_panel, name='Panel sprzedawcy'),
    url(r'^panelsprzedawcy/programkasowy/$', views.cash_register, name='Program kasowy'),
    url(r'panelsprzedawcy/programkasowy/(\d+)/$', views.transaction_summary, name='Podsumowanie transakcji'),
    url(r'^panelsprzedawcy/magazyn/$', views.warehouse, name='Magazyn'),
    url(r'^panelsprzedawcy/sprzedaz/$', views.sale_seller, name='Sprzedaż'),
    url(r'^panelsprzedawcy/ksk/$', views.ksk, name='Karta stałego klienta'),
    url(r'^panelcentralny/$', views.central_panel, name='Panel centralny'),
    url(r'^panelcentralny/obroty/$', views.sales, name='Obroty'),
    url(r'^panelcentralny/stok/$', views.stock, name='Stok'),
    url(r'^panelcentralny/zarzadzanie/$', views.management, name='Zarządzanie'),
    url(r'^panelcentralny/wyniki/$', views.sales_records, name='Wyniki'),
    url(r'^panelcentralny/kontakt/$', views.contact, name='Kontakt'),
    url(r'^panelcentralny/stoiska/$', views.stands, name='Stoiska'),
    url(r'^panelcentralny/stoiska/tworzeniestoiska/$', views.stand_creation, name='Tworzenie stoiska')
]
