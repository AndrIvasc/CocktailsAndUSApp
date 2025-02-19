from django import forms
from django.forms import inlineformset_factory
from .models import Profile, User, BartenderCocktailList, Cocktail, CocktailIngredient


class ProfileUpdateForm(forms.ModelForm):
    """Update form for profile picture. Removes the check mark to for clearing the curent profile pic"""
    profile_picture = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'clearable': False})
    )

    class Meta:
        model = Profile
        fields = ('profile_picture',)


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email',)


class BartenderCocktailListForm(forms.ModelForm):
    class Meta:
        model = BartenderCocktailList
        fields = ['name', 'is_public']


class BartenderListForm(forms.ModelForm):
    """Form for creating a bartender's cocktail list."""

    class Meta:
        model = BartenderCocktailList
        fields = ["name", "is_public"]


class AddCocktailToListForm(forms.Form):
    """Form for adding a cocktail to a bartender's list."""
    cocktail = forms.ModelChoiceField(
        queryset=Cocktail.objects.filter(is_classic=True),
        empty_label="Select a classic cocktail",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class CustomizeCocktailForm(forms.ModelForm):
    """Form for modifying a classic cocktail and saving as a custom version."""
    add_to_list = forms.ModelChoiceField(
        queryset=BartenderCocktailList.objects.none(),
        required=False,
        label="Add to Your List",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Cocktail
        fields = ["name", "image", "instructions", "glass_type", "alcoholic_strength", "category"]

    def __init__(self, *args, **kwargs):
        bartender = kwargs.pop("bartender", None)
        super().__init__(*args, **kwargs)
        if bartender:
            self.fields["add_to_list"].queryset = BartenderCocktailList.objects.filter(owner=bartender)


IngredientFormSet = inlineformset_factory(
    Cocktail, CocktailIngredient, fields=("ingredient", "amount"), extra=5
)
