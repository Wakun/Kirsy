from django.conf.urls import url

from . import views

app_name = 'page'

urlpatterns = [
    url(r'^$', views.homepage, name='homepage')
]