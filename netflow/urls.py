from django.conf.urls import url

from . import views

app_name = 'netflow'

urlpatterns = [
    url(r'^$', views.index, name='index'),
]