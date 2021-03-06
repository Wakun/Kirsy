# from django.db.models import Sum
import datetime
import itertools as it
import json
from operator import itemgetter

import django_tables2 as tables
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template import loader
from django.utils import timezone
from django_tables2 import A

from .forms import KskForm, StandForm, StandCreationForm, TransactionForm, SalesDateForm, \
    PriceForm, KskCentralForm, StandChoice, PluNumberChoice, OrderForm
from .models import Product, Ksk, Transaction, Stand, Order
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

        total_for_discount_value = total

        if transaction.is_ksk == True:
            ksk = Ksk.objects.get(card_number=transaction.ksk_num)
            if ksk.discount != 0:
                ksk_discount_value = ksk.discount / 100
                total = total - total * ksk_discount_value
                transaction.discount_value = total_for_discount_value * ksk_discount_value
                transaction.is_discount = True


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

        total_discount_value = 0.0

        all_products = []

        for obj in transactions:
            total_discount_value += obj.discount_value
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

        return render(request, 'panel/seller_sales.html', {'sales': table, 'date_form': date_form, 'date': date, 'discount_value': total_discount_value})

    else:
        group = request.user.groups.all()[0]
        date_now = datetime.datetime.now().date()

        transactions = Transaction.objects.filter(transaction_date__date=date_now, is_paid=True)

        total_discount_value = 0.0

        all_products = []

        for obj in transactions:
            total_discount_value += obj.discount_value
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

        return render(request, 'panel/seller_sales.html', {'sales': table, 'date_form': date_form, 'date': date_now, 'discount_value': total_discount_value})


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

        total_discount_value = 0.0

        all_products = []

        for obj in transactions:
            total_discount_value += obj.discount_value
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

        return render(request, 'panel/central_sales.html', {'sales': table, 'date_form': date_form, 'date': date, 'discount_value': total_discount_value})

    else:

        date_now = datetime.datetime.now().date()
        transactions = Transaction.objects.filter(transaction_date__date=date_now, is_paid=True)

        total_discount_value = 0.0

        all_products = []

        for obj in transactions:
            total_discount_value += obj.discount_value
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

        return render(request, 'panel/central_sales.html', {'sales': table, 'date_form': date_form, 'date': date_now, 'discount_value': total_discount_value})


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

@login_required(login_url='/login')
def product_view(request, pk):

     product = get_object_or_404(Product, pk=pk)

     return render(request, 'panel/product_view.html', {'product': product})


@login_required(login_url='/login')
def management(request):

        return render(request, 'panel/management.html')



@login_required(login_url='/login')
def price_changes_stand_choice(request):

    if request.method == 'POST':
        form = StandChoice(request.POST)

        if form.is_valid():
            owner = form.cleaned_data['owner']

            return redirect('panel:Wybór plu zmiany cen', owner)
    else:
        form = StandChoice()
    
    return render(request, 'panel/stand_choice.html', {'form': form})

@login_required(login_url='/login')
def price_changes_plu_choice(request, owner):

    owner = owner

    if request.method == 'POST':
        form = PluNumberChoice(request.POST)

        if form.is_valid():
            plu_num = form.cleaned_data['plu_num']
            
            return redirect('panel:Zmiana ceny', owner, plu_num)
            
    else:
        form = PluNumberChoice()

    return render(request, 'panel/plu_choice.html', {'form': form})


@login_required(login_url='/login')
def price_changes(request, owner, plu):

    owner = Group.objects.get(name=owner)
    form = PriceForm(request.POST)

    try:
        product = Product.objects.get(owner=owner, plu_num=plu)
    except Product.DoesNotExist:
        raise Http404('Nie ma takiego produktu')

    if request.method == 'POST':

        if form.is_valid():
            new_csb = form['sales_price_brutto'].value()
            product.sales_price_brutto = float(new_csb)
            product.save()
            return redirect('panel:Zmiana ceny', owner, plu)

    else:
        form = PriceForm()

    return render(request, 'panel/productprice.html', {'form': form, 'product': product, 'owner': owner})


@login_required(login_url='/login')
def orders_stand_choice(request):

    if request.method == 'POST':
        form = StandChoice(request.POST)

        if form.is_valid():
            owner = form.cleaned_data['owner']

            return redirect('panel:Wybór plu zamówienia', owner)
    else:
        form = StandChoice()
    
    return render(request, 'panel/stand_choice.html', {'form': form})


@login_required(login_url='/login')
def orders_plu_choice(request, owner):
    
    owner = owner

    if request.method == 'POST':
        form = PluNumberChoice(request.POST)

        if form.is_valid():
            plu_num = form.cleaned_data['plu_num']
            
            return redirect('panel:Zamówienia', owner, plu_num)
            
    else:
        form = PluNumberChoice()

    return render(request, 'panel/plu_choice.html', {'form': form})


@login_required(login_url='/login')
def orders(request, owner, plu):
    
    owner = Group.objects.get(name=owner)
    
    try:
        product = Product.objects.get(owner=owner, plu_num=plu)
    except Product.DoesNotExist:
        raise Http404('Nie ma produktu o takim PLU')
    
    if request.method == 'POST':
        
        form = OrderForm(request.POST)
        
        if form.is_valid():
            cz = form.cleaned_data['purchase_price']
            quantity = form.cleaned_data['quantity']
            
            new_order = Order()
            new_order.plu_num = plu
            new_order.quantity = quantity
            new_order.purchase_price = cz
            new_order.owner = owner
            new_order.save()

            product.stock += quantity
            product.save()

            return redirect('panel:Wybór plu zamówienia', owner)
            
    else:
        form = OrderForm()
        
        
        

    return render(request, 'panel/orders.html', {'form': form})


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


class KskViewTable(tables.Table):

    card_number = tables.Column()
    name = tables.Column()
    surname = tables.Column()
    city = tables.Column()
    email = tables.Column()
    phone_numer = tables.Column()
    purchase_value = tables.Column()
    discount = tables.Column()
    points = tables.Column()
    view_link = tables.LinkColumn('panel:kskdetails', args=[A('pk')], text='Szczegóły/Edycja', empty_values = ())
    

@login_required(login_url='/login')
def ksk_view(request):

    try:
        ksk = Ksk.objects.all()
    except Ksk.DoesNotExist:
        raise Http404('Nie ma kart stałego klienta')

    table = KskViewTable(ksk)
    tables.RequestConfig(request).configure(table)

    return render(request, 'panel/ksk_view.html', {'ksk': table})


@login_required(login_url='/login')
def ksk_view_details(request, pk):

    ksk = get_object_or_404(Ksk, pk=pk)

    if request.method == 'POST':
        form = KskCentralForm(request.POST, instance=ksk)
        if form.is_valid():
            ksk = form.save()
            ksk.save()
            return redirect('panel:Kartysk')
    else:
        form = KskCentralForm(instance=ksk)

    return render(request, 'panel/ksk_view_details.html', {'form': form})


@login_required(login_url='/login')
def sales_records(request):

    return HttpResponse('Wyniki')
    

@login_required(login_url='/login')
def contact(request):

    return HttpResponse('Kontakt')
