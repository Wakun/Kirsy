import django_tables2 as tables


class CentralSalesTable(tables.Table):
    plu_num = tables.Column(verbose_name='PLU')
    art_name = tables.Column(verbose_name='Nazwa artykułu')
    sales_price_brutto = tables.Column(verbose_name='Cena')
    stock = tables.Column(verbose_name='Stok')
    margin = tables.Column(verbose_name='Marża')
    zloty_margin = tables.Column(verbose_name='Marża PLN')
    temporary_quantity = tables.Column(verbose_name='Ilość')
    sale = tables.Column(verbose_name='Obrót')
    owner = tables.Column(verbose_name='Stoisko', attrs={'td': {'id': 'owner'}})


class SellerSalesTable(tables.Table):
    plu_num = tables.Column(verbose_name='PLU')
    art_name = tables.Column(verbose_name='Nazwa artykułu')
    sales_price_brutto = tables.Column(verbose_name='Cena')
    stock = tables.Column(verbose_name='Stok')
    temporary_quantity = tables.Column(verbose_name='Ilość')
    sale = tables.Column(verbose_name='Obrót')
