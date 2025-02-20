from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Cocktail, User, BartenderCocktailList, BartenderCocktailListCocktail, CocktailIngredient, \
    UserFavoriteList
from .utils import check_pasword
from .forms import ProfileUpdateForm, UserUpdateForm, BartenderListForm, AddCocktailToListForm, CustomizeCocktailForm, \
    IngredientFormSet, CreateCocktailForm


def index(request):
    return render(request, 'index.html')


"""<<<<<<<<<<<<<Classic coctail list>>>>>>>>>>>>>>>>>"""


def search_cocktails(request):
    """
    Search for Cocktails by name or category name.
    """
    query_text = request.GET.get('q', '')
    search_results = []

    if query_text:
        search_results = Cocktail.objects.filter(
            Q(name__icontains=query_text) |
            Q(category__name__icontains=query_text)
        )

    context = {'query_text': query_text, 'cocktails': search_results}
    return render(request, 'search_results.html', context)


def cocktail_list(request):
    """
    View to display all classic cocktails with pagination.
    """
    cocktails = Cocktail.objects.filter(is_classic=True)  # Only show classic cocktails
    paginator = Paginator(cocktails, 5)
    page_number = request.GET.get("page")
    paged_cocktails = paginator.get_page(page_number)

    context = {"cocktails": paged_cocktails}
    return render(request, "cocktails/cocktail_list.html", context)


def cocktail_detail(request, cocktail_id):
    """
    View to display detailed information about a single classic cocktail.
    """
    cocktail = get_object_or_404(Cocktail, id=cocktail_id)

    context = {"cocktail": cocktail}
    return render(request, "cocktails/cocktail_detail.html", context)


def public_lists(request):
    """Displays all publicly available cocktail lists from bartenders and users."""
    bartender_lists = BartenderCocktailList.objects.filter(is_public=True)
    user_lists = UserFavoriteList.objects.filter(is_public=True)

    context = {
        "bartender_lists": bartender_lists,
        "user_lists": user_lists,
    }
    return render(request, "cocktails/public_lists.html", context)


"""<<<<<<<<<<<<<Classic coctail list>>>>>>>>>>>>>>>>>"""
"""<<<<<<<<<<<<<bartender func>>>>>>>>>>>>>>>>>"""


@login_required
def bartender_lists(request):
    """
    View to display all bartender-created lists.
    """
    if not request.user.groups.filter(name="bartender").exists():
        messages.error(request, "You must be a bartender to access this page.")
        return redirect("cocktail-list")  # Redirect regular users

    user_lists = BartenderCocktailList.objects.filter(owner=request.user.profile)
    public_lists = BartenderCocktailList.objects.filter(is_public=True).exclude(owner=request.user.profile)

    context = {
        "user_lists": user_lists,
        "public_lists": public_lists,
    }
    return render(request, "cocktails/bartender_lists.html", context)


@login_required
def create_bartender_list(request):
    """
    View for bartenders to create a new cocktail list.
    """
    if not request.user.groups.filter(name="bartender").exists():
        messages.error(request, "You must be a bartender to create a list.")
        return redirect("cocktail-list")

    if request.method == "POST":
        form = BartenderListForm(request.POST)
        if form.is_valid():
            new_list = form.save(commit=False)
            new_list.owner = request.user.profile  # Assign the current user's profile
            new_list.save()
            messages.success(request, "Cocktail list created successfully!")
            return redirect("bartender-lists")
    else:
        form = BartenderListForm()

    context = {"form": form}
    return render(request, "cocktails/create_bartender_list.html", context)


@login_required
def add_cocktail_to_list(request, list_id):
    """
    Allows bartenders to add cocktails to their lists.
    """
    cocktail_list = get_object_or_404(BartenderCocktailList, id=list_id, owner=request.user.profile)

    if request.method == "POST":
        form = AddCocktailToListForm(request.POST)
        if form.is_valid():
            selected_cocktail = form.cleaned_data["cocktail"]
            BartenderCocktailListCocktail.objects.create(bartender_list=cocktail_list, cocktail=selected_cocktail)
            messages.success(request, "Cocktail added successfully!")
            return redirect("bartender-lists")
    else:
        form = AddCocktailToListForm()

    context = {"form": form, "cocktail_list": cocktail_list}
    return render(request, "cocktails/add_cocktail_to_list.html", context)


@login_required
def remove_cocktail_from_list(request, list_id, cocktail_id):
    """
    Allows bartenders to remove a cocktail from their own list.
    """
    bartender_list = get_object_or_404(BartenderCocktailList, id=list_id, owner=request.user.profile)
    cocktail_entry = get_object_or_404(BartenderCocktailListCocktail, bartender_list=bartender_list,
                                       cocktail_id=cocktail_id)

    if request.method == "POST":
        cocktail_entry.delete()
        messages.success(request, "Cocktail removed successfully!")
        return redirect("bartender-lists")

    context = {
        "bartender_list": bartender_list,
        "cocktail": cocktail_entry.cocktail
    }
    return render(request, "cocktails/remove_cocktail_confirm.html", context)


@login_required
def customize_cocktail(request, cocktail_id):
    """
    Allows bartenders to modify a classic cocktail and save it as a new version.
    If the cocktail is not classic, it cannot be customized.
    """
    original_cocktail = get_object_or_404(Cocktail, id=cocktail_id)

    # Only allow customization of classic cocktails
    if not original_cocktail.is_classic:
        messages.error(request, "You can only customize classic cocktails.")
        return redirect("cocktail-detail", cocktail_id=original_cocktail.id)

    old_image = original_cocktail.image  # Preserve old image

    if request.method == "POST":
        form = CustomizeCocktailForm(request.POST, request.FILES, bartender=request.user.profile)
        ingredient_formset = IngredientFormSet(request.POST)

        if form.is_valid() and ingredient_formset.is_valid():
            # Create a new custom cocktail (copy of the classic one)
            new_cocktail = form.save(commit=False)
            new_cocktail.is_classic = False
            new_cocktail.original_cocktail = original_cocktail
            new_cocktail.bartender = request.user
            new_cocktail.category = original_cocktail.category
            new_cocktail.save()

            # Preserve old image if no new one is uploaded
            if not request.FILES.get("image"):
                new_cocktail.image = old_image
                new_cocktail.save()

            # Assign the new cocktail instance to the formset before saving
            ingredient_formset.instance = new_cocktail
            ingredient_formset.save()

            bartender_list = form.cleaned_data.get("add_to_list")
            if bartender_list:
                bartender_list.bartendercocktaillistcocktail_set.create(cocktail=new_cocktail)

            messages.success(request, "Cocktail saved successfully!")
            return redirect("cocktail-detail", cocktail_id=new_cocktail.id)

        messages.error(request, "There was an error saving the cocktail. Please check the form.")

    else:
        # Load existing ingredients from the classic cocktail
        ingredient_queryset = CocktailIngredient.objects.filter(cocktail=original_cocktail)

        # Pre-fill the formset with the existing ingredients (editable)
        ingredient_formset = IngredientFormSet(queryset=ingredient_queryset)

        # Create the form using the classic cocktail's data
        form = CustomizeCocktailForm(instance=original_cocktail, bartender=request.user.profile)

    context = {
        "form": form,
        "ingredient_formset": ingredient_formset,
        "original_cocktail": original_cocktail,
    }

    return render(request, "cocktails/customize_cocktail.html", context)


@login_required
def create_cocktail(request):
    """
    Allows bartenders to create a new cocktail from scratch.
    """
    if request.method == "POST":
        form = CreateCocktailForm(request.POST, request.FILES, bartender=request.user.profile)
        ingredient_formset = IngredientFormSet(request.POST)

        if form.is_valid() and ingredient_formset.is_valid():
            new_cocktail = form.save(commit=False)
            new_cocktail.is_classic = False  # ✅ Ensure it's not a classic cocktail
            new_cocktail.bartender = request.user
            new_cocktail.save()

            # ✅ Save the ingredients
            ingredient_formset.instance = new_cocktail
            ingredient_formset.save()

            # ✅ Save to bartender's list
            bartender_list = form.cleaned_data.get("add_to_list")
            if bartender_list:
                bartender_list.bartendercocktaillistcocktail_set.create(cocktail=new_cocktail)

            messages.success(request, "Cocktail created successfully!")
            return redirect("cocktail-detail", cocktail_id=new_cocktail.id)

    else:
        form = CreateCocktailForm(bartender=request.user.profile)
        ingredient_formset = IngredientFormSet(queryset=CocktailIngredient.objects.none())

    context = {
        "form": form,
        "ingredient_formset": ingredient_formset,
    }

    return render(request, "cocktails/create_cocktail.html", context)


"""<<<<<<<<<<<<<bartender func>>>>>>>>>>>>>>>>>"""
"""<<<<<<<<<<<<<Profile user func>>>>>>>>>>>>>>>>>"""


@csrf_protect
def register_user(request):
    """User registry handling"""
    if request.method == 'GET':
        return render(request, 'registration/registration.html')

    elif request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if not check_pasword(password):
            messages.error(request, 'Password has to be 8 symbols or more!')
            return redirect('register')
        if password != password2:
            messages.error(request, 'Passwords dont match!')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username {username} already taken!')
            return redirect('register')
        if User.objects.filter(email=email).exists():
            messages.error(request, f'Email {email} already taken!')
            return redirect('register')
        User.objects.create_user(username=username, email=email, password=password)
        messages.info(request, f'User {username} registered!')
        return redirect('login')


@login_required()
def get_user_profile(request):
    if request.method == 'POST':
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            messages.info(request, "Profile updated")
        else:
            messages.error(request, "Profile not updated")
        return redirect('user-profile')
    p_form = ProfileUpdateForm(instance=request.user.profile)
    u_form = UserUpdateForm(instance=request.user)
    context = {
        'p_form': p_form,
        'u_form': u_form
    }
    return render(request, 'profile.html', context=context)


"""<<<<<<<<<<<<<Profile user func>>>>>>>>>>>>>>>>>"""
