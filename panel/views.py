# from django.db.models import Sum
import datetime
import itertools as it
import json
from operator import itemgetter

import django_tables2 as tables
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.utils import timezone
from django_tables2 import A

from .forms import KskForm, StandForm, StandCreationForm, TransactionForm, SalesDateForm, \
    PriceChangesChoice, PriceAndPromoForm
from .models import Product, Ksk, Transaction, Stand
from .tables import CentralSalesTable, SellerSalesTable


# from django.contrib.auth.models import Group


@login_required(login_url='/login')
def index(request):
    now = datetime.datetime.now()
    template = loader.get_template('panel/index.html')
    context = {'date': now}

    return HttpResponse(template.render(context, request))


@login_required(login_url='/login')
def seller_panel(request):
    now = datetime.datetime.now()
    template = loader.get_template('panel/seller_panel.html')
    context = {'date': now}

    return HttpResponse(template.render(context, request))


@login_required(login_url='/login')
def cash_register(request):

    if request.method == 'POST':
        plulist = request.POST.get('plulist')
        quantitylist = request.POST.get('quant')
        ksk_number = request.POST.get('ksk_num')

        if not (plulist or quantitylist):
            raise Http404('Transakcja nie może być pusta!')

        plulist = [int(x) for x in plulist[:-1].split(',')]
        quantitylist = [int(x) for x in quantitylist[:-1].split(',')]

        allplu = {k: 0 for k in plulist}

        for x in range(len(plulist)):
            for plu in allplu:
                if plulist[x] == plu:
                    allplu[plu] += quantitylist[x]

        try:
            assert type(allplu) is dict
        except AssertionError:
            raise Exception('Cannot create dictionary of transaction.')

        newtrans = Transaction()
        newtrans.set_plu_list(allplu)
        newtrans.owner = request.user

        if ksk_number:
            try:
                card_number = Ksk.objects.get(card_number=ksk_number)
                newtrans.is_ksk = True
                newtrans.ksk_num = card_number.card_number
            except Ksk.DoesNotExist:
                raise Http404('Brak karty o takim numerze')

        newtrans.save()
        trans_id = newtrans.id
        return redirect('panel:Podsumowanie transakcji', trans_id)

    else:

        try:

            try:
                group = request.user.groups.all()[0]
            except:
                raise Http404('User has no group assigned.')

            products = Product.objects.filter(owner=group).values_list('plu_num', 'art_name', 'sales_price_brutto')
            products_json = json.dumps(list(products), cls=DjangoJSONEncoder)
        except Product.DoesNotExist:
            raise Http404('Products cant\'t be found!')

        return render(request, 'panel/cash_register.html', {'products_json': products_json})


@login_required(login_url='/login')
def transaction_summary(request, id):

    if request.method == 'POST':

        form = TransactionForm(request.POST)

        is_paid = form['is_paid'].value()

        group = request.user.groups.all()[0]

        transaction = Transaction.objects.get(id=id)
        transaction.is_paid = is_paid
        transaction.save()

        if is_paid == True:
            allplu = transaction.get_plu_list()

            for prod in allplu:
                obj = Product.objects.get(owner=group, plu_num=prod)

                obj.stock -= allplu[prod]
                obj.quantity_sold += allplu[prod]
                obj.temporary_quantity = allplu[prod]
                obj.save()

        if is_paid == True and transaction.is_ksk == True:
            ksk = Ksk.objects.get(card_number=transaction.ksk_num)
            ksk.points += round(transaction.total / 10)
            ksk.purchase_value += transaction.total
            ksk.save()

        return redirect('panel:Program kasowy')

    else:

        transaction = Transaction.objects.get(id=id)
        allplu = transaction.get_plu_list()

        group = request.user.groups.all()[0]

        total = 0.0
        for prod in allplu:
            obj = Product.objects.get(owner=group, plu_num=prod)
            total += obj.sales_price_brutto * allplu[prod]

        transaction.total = total
        transaction.save()

        transactionform = TransactionForm

        return render(request, 'panel/transaction_summary.html', {'transaction': transaction, 'total': total, 'transactionform': transactionform})


@login_required(login_url='/login')
def warehouse(request):
    try:
        stocks = Product.objects.only('plu_num', 'art_name', 'stock')
    except Product.DoesNotExist:
        raise Http404('Products can\'t be found!')
    return render(request, 'panel/seller_warehouse.html', {'stocks': stocks})


@login_required(login_url='/login')
def sale_seller(request):

    if request.method == 'POST':

        group = request.user.groups.all()[0]

        form = SalesDateForm(request.POST)

        date = form['date'].value()
        date = datetime.datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")

        transactions = Transaction.objects.filter(transaction_date__date=date, is_paid=True)

        all_products = []

        for obj in transactions:
            allplu = obj.get_plu_list()
            for prod in allplu:
                product = Product.objects.get(owner=group, plu_num=int(prod))
                all_products.append(product.history.as_of(obj.transaction_date + datetime.timedelta(seconds=3)))

        for prod in all_products:
            most_recent_stock = Product.objects.get(plu_num=prod.plu_num, owner=group).stock
            prod.stock = most_recent_stock

        transaction_json = serializers.serialize('python', list(all_products), fields=('plu_num', 'art_name',
                                                                                       'sales_price_brutto', 'stock',
                                                                                       'temporary_quantity'))
        data = [d['fields'] for d in transaction_json]

        new_data = []
        for item in data:
            item = dict(item)
            new_data.append(item)

        keyfunc = itemgetter('plu_num', 'sales_price_brutto', 'art_name')

        groups = ((plu, price, art_name, list(g))
                  for (plu, price, art_name), g in it.groupby(sorted(new_data, key=keyfunc), keyfunc))
        table_data = [{'plu_num': plu, 'art_name': art_name, 'sales_price_brutto': price, 'stock': g[0]['stock'],
              'temporary_quantity': sum(x['temporary_quantity'] for x in g),
                       'sale': sum(x['temporary_quantity'] for x in g) * price}
             for plu, price, art_name, g in groups]

        table = SellerSalesTable(table_data)
        tables.RequestConfig(request).configure(table)
        date_form = SalesDateForm

        return render(request, 'panel/seller_sales.html', {'sales': table, 'date_form': date_form, 'date': date})

    else:
        group = request.user.groups.all()[0]
        date_now = datetime.datetime.now().date()

        transactions = Transaction.objects.filter(transaction_date__date=date_now, is_paid=True)

        all_products = []

        for obj in transactions:
            allplu = obj.get_plu_list()
            for prod in allplu:
                product = Product.objects.get(owner=group, plu_num=int(prod))
                all_products.append(product.history.as_of(obj.transaction_date + datetime.timedelta(seconds=3)))

        for prod in all_products:
            most_recent_stock = Product.objects.get(plu_num=prod.plu_num, owner=group).stock
            prod.stock = most_recent_stock

        transaction_json = serializers.serialize('python', list(all_products), fields=('plu_num', 'art_name',
                                                                                       'sales_price_brutto', 'stock',
                                                                                       'temporary_quantity'))
        data = [d['fields'] for d in transaction_json]

        new_data = []
        for item in data:
            item = dict(item)
            new_data.append(item)

        keyfunc = itemgetter('plu_num', 'sales_price_brutto', 'art_name')

        groups = ((plu, price, art_name, list(g))
                  for (plu, price, art_name), g in it.groupby(sorted(new_data, key=keyfunc), keyfunc))
        table_data = [{'plu_num': plu, 'art_name': art_name, 'sales_price_brutto': price, 'stock': g[0]['stock'],
              'temporary_quantity': sum(x['temporary_quantity'] for x in g),
                       'sale': sum(x['temporary_quantity'] for x in g) * price}
             for plu, price, art_name, g in groups]

        table = SellerSalesTable(table_data)
        tables.RequestConfig(request).configure(table)

        date_form = SalesDateForm

        return render(request, 'panel/seller_sales.html', {'sales': table, 'date_form': date_form, 'date': date_now})


@login_required(login_url='/login')
def ksk(request):
    if request.method == 'POST':
        form = KskForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user  # ??
            post.published_date = timezone.now()  # ??
            post.save()  # ??
            return redirect('panel:Karta stałego klienta')
    else:
        form = KskForm()
    return render(request, 'panel/kskregister.html', {'form': form})


@login_required(login_url='/login')
def central_panel(request):
    now = datetime.datetime.now()
    template = loader.get_template('panel/central_panel.html')
    context = {'date': now}

    return HttpResponse(template.render(context, request))


@login_required(login_url='/login')
def sales(request):

    if request.method == 'POST':

        form = SalesDateForm(request.POST)

        date = form['date'].value()
        date = datetime.datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")

        transactions = Transaction.objects.filter(transaction_date__date=date, is_paid=True)

        all_products = []

        for obj in transactions:
            allplu = obj.get_plu_list()
            for prod in allplu:
                product = Product.objects.get(plu_num=int(prod), owner=obj.owner.groups.all()[0])
                all_products.append(product.history.as_of(obj.transaction_date + datetime.timedelta(seconds=3)))

        for prod in all_products:
            most_recent_stock = Product.objects.get(plu_num=prod.plu_num, owner=prod.owner).stock
            prod.stock = most_recent_stock

        transaction_json = serializers.serialize('python', list(all_products), fields=(
            'plu_num', 'art_name', 'sales_price_brutto', 'stock', 'temporary_quantity', 'margin', 'zloty_margin',
            'owner_name'))
        data = [d['fields'] for d in transaction_json]

        new_data = []
        for item in data:
            item = dict(item)
            new_data.append(item)

        keyfunc = itemgetter('plu_num', 'sales_price_brutto', 'art_name', 'margin', 'owner_name')

        groups = ((plu, price, art_name, margin, owner, list(g))
                  for (plu, price, art_name, margin, owner), g in it.groupby(sorted(new_data, key=keyfunc), keyfunc))

        table_data = [{'plu_num': plu, 'art_name': art_name, 'sales_price_brutto': price, 'stock': g[0]['stock'],
                       'temporary_quantity': sum(x['temporary_quantity'] for x in g),
                       'sale': sum(x['temporary_quantity'] for x in g) * price,
                       'owner': owner, 'margin': margin,
                       'zloty_margin': (sum(x['temporary_quantity'] for x in g) * price) * (margin / 100)} for
                      plu, price, art_name, margin, owner, g in groups]

        table = CentralSalesTable(table_data)
        tables.RequestConfig(request).configure(table)
        date_form = SalesDateForm

        return render(request, 'panel/central_sales.html', {'sales': table, 'date_form': date_form, 'date': date})

    else:

        date_now = datetime.datetime.now().date()
        transactions = Transaction.objects.filter(transaction_date__date=date_now, is_paid=True)

        all_products = []

        for obj in transactions:
            allplu = obj.get_plu_list()
            for prod in allplu:
                product = Product.objects.get(plu_num=int(prod), owner=obj.owner.groups.all()[0])
                all_products.append(product.history.as_of(obj.transaction_date + datetime.timedelta(seconds=3)))

        for prod in all_products:
            most_recent_stock = Product.objects.get(plu_num=prod.plu_num, owner=prod.owner).stock
            prod.stock = most_recent_stock

        transaction_json = serializers.serialize('python', list(all_products), fields=(
                                                                         'plu_num', 'art_name',
                                                                         'sales_price_brutto', 'stock',
                                                                         'temporary_quantity',
                                                                         'margin', 'zloty_margin', 'owner_name'))
        data = [d['fields'] for d in transaction_json]

        new_data = []
        for item in data:
            item = dict(item)
            new_data.append(item)

        keyfunc = itemgetter('plu_num', 'sales_price_brutto', 'art_name', 'margin', 'owner_name')

        groups = ((plu, price, art_name, margin, owner, list(g))
                  for (plu, price, art_name, margin, owner), g in it.groupby(sorted(new_data, key=keyfunc), keyfunc))

        table_data = [{'plu_num': plu, 'art_name': art_name, 'sales_price_brutto': price, 'stock': g[0]['stock'],
                       'temporary_quantity': sum(x['temporary_quantity'] for x in g), 'sale': sum(x['temporary_quantity'] for x in g) * price,
                       'owner': owner, 'margin': margin,
                       'zloty_margin': (sum(x['temporary_quantity'] for x in g) * price) * (margin / 100)} for plu, price, art_name, margin, owner, g in groups]

        table = CentralSalesTable(table_data)
        tables.RequestConfig(request).configure(table)
        date_form = SalesDateForm

        return render(request, 'panel/central_sales.html', {'sales': table, 'date_form': date_form, 'date': date_now})

class StockTable(tables.Table):

    plu_num = tables.Column()
    art_name = tables.Column()
    purchase_price_netto = tables.Column()
    purchase_price_brutto = tables.Column()
    sales_price_netto = tables.Column()
    sales_price_brutto = tables.Column()
    vat_value = tables.Column()
    vat_difference = tables.Column()
    margin = tables.Column()
    zloty_margin = tables.Column()
    stock = tables.Column()
    stock_cz_pln = tables.Column()
    stock_cs_pln = tables.Column()
    owner_name = tables.Column()
    view_link = tables.LinkColumn('panel:Widok produktu', args=[A('pk')], text='Szczegóły', empty_values = ())


@login_required(login_url='/login')
def stock(request):

    try:
        products = Product.objects.all()
    except Product.DoesNotExist:
        raise Http404('Brak produktów')

    table = StockTable(products)
    tables.RequestConfig(request).configure(table)

    return render(request, 'panel/central_stock.html', {'stocks': table})

@login_required(login_url='\login')
def product_view(request, pk):

     product = get_object_or_404(Product, pk=pk)

     return render(request, 'panel/product_view.html', {'product': product})


@login_required(login_url='/login')
def management(request):

    return render(request, 'panel/management.html')


@login_required(login_url='/login')
def price_changes(request):

    if request.method == 'POST':
        form = PriceChangesChoice(request.POST)

        if form.is_valid():
            plu_num = form.cleaned_data['plu_num']
            owner = form.cleaned_data['owner']

            try:
                product = Product.objects.get(plu_num=plu_num, owner=owner)
            except Product.DoesNotExist:
                raise Http404('Nie ma takiego produktu.')

            prod_id = product.id

            return redirect('panel:Zmiana ceny', prod_id)

    else:
        form = PriceChangesChoice()

    return render(request, 'panel/price_changes.html', {'form': form})


@login_required(login_url='/login')
def priceandpromo(request, id):

    form = PriceAndPromoForm(request.POST)

    product = Product.objects.get(id=id)

    if request.method == 'POST':

        if form.is_valid():
            new_csb = form['sales_price_brutto'].value()
            product.sales_price_brutto = float(new_csb)
            product.save()
            return redirect('panel:Zmiana ceny', product.id)

    else:
        form = PriceAndPromoForm()

    return render(request, 'panel/productprice.html', {'form': form, 'product': product})




@login_required(login_url='/login')
def orders(request):

    return HttpResponse('Zamówienia')


@login_required(login_url='/login')
def stands(request):
    try:
        stands = Stand.objects.all()
    except Stand.DoesNotExist:
        raise Http404

    return render(request, 'panel/central_stands.html', {'stands': stands})


@login_required(login_url='/login')
def stand_creation(request):
    if request.method == 'POST':
        form1 = StandCreationForm(request.POST)
        form2 = StandForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            form1.save()
            form2.save()
            username = form1.cleaned_data.get('username')
            raw_password = form1.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('panel:Stoiska')
    else:
        form1 = StandCreationForm
        form2 = StandForm

    return render(request, 'panel/central_stand_creation.html', {'form1': form1, 'form2': form2})


@login_required(login_url='/login')
def sales_records(request):
    return HttpResponse('Wyniki')


@login_required(login_url='/login')
def contact(request):
    return HttpResponse('Kontakt')
