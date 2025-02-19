from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('coctails/search/', views.search_cocktails, name='search'),
    path('register/', views.register_user, name='register'),
    path('profile/', views.get_user_profile, name='user-profile'),
    path('cocktails/', views.cocktail_list, name='cocktail-list'),
    path('cocktails/<int:cocktail_id>/', views.cocktail_detail, name='cocktail-detail'),
    path("bartender/lists/", views.bartender_lists, name="bartender-lists"),
    path("bartender/lists/create/", views.create_bartender_list, name="create-bartender-list"),
    path("bartender/lists/<int:list_id>/add-cocktail/", views.add_cocktail_to_list, name="add-cocktail-to-list"),
    path("bartender/lists/<int:list_id>/remove/<int:cocktail_id>/", views.remove_cocktail_from_list,
         name="remove-cocktail-from-list"),
    path("cocktails/customize/<int:cocktail_id>/", views.customize_cocktail, name="customize-cocktail"),
]
