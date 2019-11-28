from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('initProfile', views.initProfile_view, name='initProfile'),
    path('updateBalance', views.updateBalance_view, name='updateBalance'),
    path('<str:betRoomName>/', views.betRoom, name='betRoom'),
    path('api/NFLUpcoming', views.nflUpcomingView, name='nflUpcomingApi'),
    path('api/NFLPlaceBet', views.nflPlaceBetView, name='nflPlaceBetApi'),
    path('orders', views.ordersView, name='orders')
]