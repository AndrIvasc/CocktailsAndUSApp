from django import forms
from .models import Profile, User


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
