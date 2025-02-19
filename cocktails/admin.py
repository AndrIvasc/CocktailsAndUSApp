from django.contrib import admin
from .models import (
    Profile, Ingredient, CocktailCategory, Cocktail, CocktailIngredient,
    UserFavoriteList, BartenderCocktailList, UserCocktailList, BartenderCocktailListCocktail
)


class CocktailIngredientInline(admin.TabularInline):
    """Inline model for displaying ingredients in a cocktail
    TabularInline is used for better UI"""
    model = CocktailIngredient
    extra = 1


@admin.register(Cocktail)
class CocktailAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'alcoholic_strength', 'is_classic')
    search_fields = ('name',)
    list_filter = ('category', 'alcoholic_strength', 'is_classic')
    inlines = [CocktailIngredientInline]


# Register other models normally
admin.site.register(Profile)
admin.site.register(Ingredient)
admin.site.register(CocktailCategory)
admin.site.register(UserFavoriteList)
admin.site.register(BartenderCocktailList)
admin.site.register(UserCocktailList)
admin.site.register(BartenderCocktailListCocktail)
