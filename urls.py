from django.urls import path
from betMaster import views

urlpatterns = [
    path('', views.index_view, name='index')

]