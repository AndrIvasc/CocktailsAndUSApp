from django.urls import path
from .views import index, search_cocktails, register_user, get_user_profile, cocktail_list, cocktail_detail

urlpatterns = [
    path('', index, name='index'),
    path('coctails/search/', search_cocktails, name='search'),
    path('register/', register_user, name='register'),
    path('profile/', get_user_profile, name='user-profile'),
    path('cocktails/', cocktail_list, name='cocktail-list'),
    path('cocktails/<int:cocktail_id>/', cocktail_detail, name='cocktail-detail'),
]
