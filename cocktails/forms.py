from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory, BaseInlineFormSet
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


class CreateCocktailForm(forms.ModelForm):
    """Form for bartenders to create a new cocktail from scratch."""

    add_to_list = forms.ModelChoiceField(
        queryset=BartenderCocktailList.objects.none(),
        required=True,
        empty_label=None,
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
            lists = BartenderCocktailList.objects.filter(owner=bartender)
            self.fields["add_to_list"].queryset = lists
            if lists.exists():
                self.fields["add_to_list"].initial = lists.first()


class CustomizeCocktailForm(forms.ModelForm):
    """Form for modifying a classic cocktail and saving it as a custom version."""

    add_to_list = forms.ModelChoiceField(
        queryset=BartenderCocktailList.objects.none(),  # Empty initially
        required=True,
        empty_label=None,  # Removes the empty space in the dropdown
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
            # Get all bartender's lists
            bartender_lists = BartenderCocktailList.objects.filter(owner=bartender)

            # Update the queryset
            self.fields["add_to_list"].queryset = bartender_lists

            # Set the first list as default if there are any
            if bartender_lists.exists():
                self.fields["add_to_list"].initial = bartender_lists.first()


class IngredientFormSetHelper(BaseInlineFormSet):
    """Custom Formset that dynamically adjusts extra fields and skips blank ones"""

    def clean(self):
        """Override validation to allow empty ingredient fields instead of marking as required"""
        super().clean()
        for form in self.forms:
            if form.cleaned_data.get("DELETE"):
                continue  # Skip validation for deleted fields

            ingredient = form.cleaned_data.get("ingredient")
            amount = form.cleaned_data.get("amount")

            # Allow empty ingredient fields (they won't be saved)
            if not ingredient and not amount:
                form.cleaned_data["DELETE"] = True  # Mark form for deletion so Django ignores it
                continue

            # If one field is filled but not the other, raise a validation error
            if not ingredient or not amount:
                raise ValidationError("Both ingredient and amount are required if one is filled.")


IngredientFormSet = inlineformset_factory(
    Cocktail,
    CocktailIngredient,
    fields=("ingredient", "amount"),
    extra=10,  # Ensures at least one blank ingredient field for new additions
    can_delete=True,  # Allows removing ingredients
    formset=IngredientFormSetHelper  # Use the custom formset
)
