from django.db import models
from django.contrib.auth.models import User
from PIL import Image


class Profile(models.Model):
    """Profile Model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(
        upload_to='profile_pics',
        default="profile_pics/default-user.png",
        blank=True,
        null=True
    )
    DRINK_PREFERENCES = [
        ('Alcoholic', 'Alcoholic'),
        ('Non-Alcoholic', 'Non-Alcoholic'),
        ('Both', 'Both')
    ]
    preferred_drink_type = models.CharField(max_length=15, choices=DRINK_PREFERENCES, default='Both')

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.profile_picture.path:
            img = Image.open(self.profile_picture.path)
            thumb_size = (200, 200)
            img.thumbnail(thumb_size)
            img.save(self.profile_picture.path)


class Ingredient(models.Model):
    """Ingredient Model"""
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=50)
    is_spirit = models.BooleanField(default=False)
    alcohol_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name


class CocktailCategory(models.Model):
    """Cocktail Category Model"""
    name = models.CharField(max_length=50)
    is_alcoholic = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# Cocktail Model
class Cocktail(models.Model):
    """Cocktail Model"""
    name = models.CharField(max_length=100)
    original_cocktail = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    bartender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(CocktailCategory, on_delete=models.CASCADE)
    instructions = models.TextField()
    image = models.ImageField(upload_to='cocktails', blank=True, null=True)
    glass_type = models.CharField(max_length=100)
    ALCOHOLIC_STRENGTH = [
        ('None', 'None'),
        ('Light', 'Light'),
        ('Medium', 'Medium'),
        ('Strong', 'Strong'),
    ]
    alcoholic_strength = models.CharField(max_length=10, choices=ALCOHOLIC_STRENGTH, default='Medium')
    is_classic = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class CocktailIngredient(models.Model):
    """Junction Table for Cocktail-Ingredient Relationship"""
    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.CharField(max_length=100, default="To taste")

    def __str__(self):
        return f"{self.amount} of {self.ingredient.name} in {self.cocktail.name}"


class UserFavoriteList(models.Model):
    """User's Favorite Cocktail List Model"""
    owner = models.OneToOneField(Profile, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.owner.user.username}'s Favorite List"


class UserCocktailList(models.Model):
    """Junction Table for User Favorite Cocktails"""
    user_list = models.ForeignKey(UserFavoriteList, on_delete=models.CASCADE)
    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.cocktail.name} in {self.user_list.owner.user.username}'s Favorites"


class BartenderCocktailList(models.Model):
    """Bartender's Cocktail List Model"""
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.owner.user.username}'s {self.name}"


class BartenderCocktailListCocktail(models.Model):
    """Junction Table for Bartender's Cocktail Lists"""
    bartender_list = models.ForeignKey(BartenderCocktailList, on_delete=models.CASCADE)
    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.cocktail.name} in {self.bartender_list.owner.user.username}'s {self.bartender_list.name}"
