from django.contrib import admin
from .models import (
    Profile, Ingredient, CocktailCategory, Cocktail, CocktailIngredient,
    UserFavoriteList, BartenderCocktailList, UserCocktailList, BartenderCocktailListCocktail,
)


class CocktailIngredientInline(admin.TabularInline):
    """Inline model for displaying ingredients in a cocktail
    TabularInline is used for better UI"""
    model = CocktailIngredient
    extra = 1


class CocktailCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_alcoholic')
    list_filter = ('is_alcoholic',)
    search_fields = ('name',)


class CocktailAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_alcoholic_display', 'bartender', 'is_classic')
    list_filter = ('is_classic', 'category__is_alcoholic')
    search_fields = ('name', 'category__name')
    list_editable = ('category',)
    fields = ('name', 'category', 'image', 'instructions', 'glass_type', 'alcoholic_strength', 'is_classic')
    inlines = [CocktailIngredientInline]  # ✅ Add ingredient editing in admin panel

    def is_alcoholic_display(self, obj):
        """Show whether the cocktail is alcoholic based on its category."""
        return obj.category.is_alcoholic if obj.category else "Unknown"

    is_alcoholic_display.short_description = "Alcoholic?"


# Register other models normally
admin.site.register(Profile)
admin.site.register(Ingredient)
admin.site.register(CocktailCategory, CocktailCategoryAdmin)
admin.site.register(Cocktail, CocktailAdmin)
admin.site.register(UserFavoriteList)
admin.site.register(BartenderCocktailList)
admin.site.register(UserCocktailList)
admin.site.register(BartenderCocktailListCocktail)
admin.site.register(CocktailIngredient)
