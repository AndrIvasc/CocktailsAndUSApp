from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import Group

from .models import Cocktail, User, BartenderCocktailList, BartenderCocktailListCocktail, CocktailIngredient, \
    UserFavoriteList, UserCocktailList, Ingredient
from .utils import check_pasword
from .forms import ProfileUpdateForm, UserUpdateForm, BartenderListForm, AddCocktailToListForm, CustomizeCocktailForm, \
    IngredientFormSet, CreateCocktailForm
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def index(request):
    """
    Display the home page with a personalized message and a cocktail image carousel.
    """
    cocktails = Cocktail.objects.exclude(image="")

    context = {
        "cocktails": cocktails,
    }
    return render(request, "index.html", context)


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
    paginator = Paginator(cocktails, 4)
    page_number = request.GET.get("page")
    paged_cocktails = paginator.get_page(page_number)

    context = {"cocktails": paged_cocktails}
    return render(request, "cocktails/cocktail_list.html", context)


def cocktail_detail(request, cocktail_id):
    """
    View to display detailed information about a single classic cocktail.
    """
    cocktail = get_object_or_404(Cocktail, id=cocktail_id)

    context = {
        "cocktail": cocktail,
    }
    return render(request, "cocktails/cocktail_detail.html", context)


def public_lists(request):
    """Displays all publicly available cocktail lists from bartenders and users."""
    bartender_lists = BartenderCocktailList.objects.filter(is_public=True)

    context = {
        "bartender_lists": bartender_lists,
    }
    return render(request, "cocktails/public_lists.html", context)


@login_required
def bartender_lists(request):
    """
    View to display all bartender-created lists.
    """
    if not request.user.groups.filter(name="bartender").exists():
        messages.error(request, "You must be a bartender to access this page.")
        return redirect("cocktail-list")  # Redirect regular users

    user_lists = BartenderCocktailList.objects.filter(owner=request.user.profile)

    context = {
        "user_lists": user_lists,
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
    If the cocktail is not in any other list and is not a classic, it gets deleted.
    """
    bartender_list = get_object_or_404(BartenderCocktailList, id=list_id, owner=request.user.profile)
    cocktail_entry = get_object_or_404(BartenderCocktailListCocktail, bartender_list=bartender_list,
                                       cocktail_id=cocktail_id)

    cocktail = cocktail_entry.cocktail

    if request.method == "POST":
        cocktail_entry.delete()

        is_in_other_lists = BartenderCocktailListCocktail.objects.filter(cocktail=cocktail).exists()
        is_in_favorites = UserCocktailList.objects.filter(cocktail=cocktail).exists()

        if not cocktail.is_classic and not is_in_other_lists and not is_in_favorites:
            cocktail.delete()
            messages.success(request, "Cocktail removed from list and deleted permanently.")
        else:
            messages.success(request, "Cocktail removed from your list.")

        return redirect("bartender-lists")

    context = {
        "bartender_list": bartender_list,
        "cocktail": cocktail
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

            # Ensure category is saved properly
            new_cocktail.category = form.cleaned_data.get("category", original_cocktail.category)

            new_cocktail.save()

            # Preserve old image if no new one is uploaded
            if not request.FILES.get("image"):
                new_cocktail.image = old_image
                new_cocktail.save()

            # Assign the new cocktail instance to the formset before saving
            ingredient_formset.instance = new_cocktail
            ingredient_formset.save()

            # Add to bartender's list if selected
            bartender_list = form.cleaned_data.get("add_to_list")
            if bartender_list:
                bartender_list.bartendercocktaillistcocktail_set.create(cocktail=new_cocktail)

            messages.success(request, "Cocktail saved successfully!")
            return redirect("cocktail-detail", cocktail_id=new_cocktail.id)

        messages.error(request, "There was an error saving the cocktail. Please check the form.")

    else:
        # Load existing ingredients from the classic cocktail
        ingredient_queryset = CocktailIngredient.objects.filter(cocktail=original_cocktail)

        # Pre-fill the formset with the existing ingredients from the classic cocktail
        ingredient_formset = IngredientFormSet(queryset=ingredient_queryset, initial=[
            {"ingredient": ing.ingredient, "amount": ing.amount} for ing in ingredient_queryset
        ])

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
            new_cocktail.is_classic = False
            new_cocktail.bartender = request.user
            new_cocktail.save()

            # Save the ingredients
            ingredient_formset.instance = new_cocktail
            ingredient_formset.save()

            # Save to bartender's list
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


@login_required
def toggle_list_visibility(request, list_id):
    """
    Toggle the visibility of a bartender's cocktail list (Public <-> Private).
    """
    bartender_list = get_object_or_404(BartenderCocktailList, id=list_id, owner=request.user.profile)

    if request.method == "POST":
        bartender_list.is_public = not bartender_list.is_public  # ✅ Toggle visibility
        bartender_list.save()
        return JsonResponse({"success": True, "is_public": bartender_list.is_public})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@login_required
def delete_list(request, list_id):
    """
    Allows a bartender to delete their own cocktail list.
    """
    bartender_list = get_object_or_404(BartenderCocktailList, id=list_id, owner=request.user.profile)

    if request.method == "POST":
        bartender_list.delete()  # Delete the list
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@login_required
def user_favorite_list(request):
    """View the user's favorite cocktail list"""
    favorite_list, created = UserFavoriteList.objects.get_or_create(owner=request.user.profile)
    favorite_cocktails = UserCocktailList.objects.filter(user_list=favorite_list)

    return render(request, "cocktails/user_favorite_list.html", {
        "favorite_list": favorite_list,
        "favorite_cocktails": favorite_cocktails,
    })


@login_required
def add_to_favorites(request, cocktail_id):
    """Add a Classic or Public Cocktail to User's Favorite List"""
    favorite_list, created = UserFavoriteList.objects.get_or_create(owner=request.user.profile)
    cocktail = get_object_or_404(Cocktail, id=cocktail_id)

    # Ensure only Classic or Public Cocktails can be added
    if not cocktail.is_classic and not BartenderCocktailListCocktail.objects.filter(cocktail=cocktail).exists():
        messages.error(request, "You can only add Classic Cocktails or Public Cocktails!")
        return redirect("cocktail-detail", cocktail_id=cocktail.id)

    # Check if the cocktail is already in favorites
    if UserCocktailList.objects.filter(user_list=favorite_list, cocktail=cocktail).exists():
        messages.warning(request, "This cocktail is already in your favorites.")
    else:
        UserCocktailList.objects.create(user_list=favorite_list, cocktail=cocktail)
        messages.success(request, "Cocktail added to favorites!")

    return redirect("cocktail-detail", cocktail_id=cocktail.id)


@login_required
def remove_from_favorites(request, cocktail_id):
    """Remove a Cocktail from the User's Favorite List"""
    favorite_list = get_object_or_404(UserFavoriteList, owner=request.user.profile)
    cocktail = get_object_or_404(Cocktail, id=cocktail_id)

    UserCocktailList.objects.filter(user_list=favorite_list, cocktail=cocktail).delete()
    messages.success(request, "Cocktail removed from favorites.")

    return redirect("user-favorite-list")


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
        user = User.objects.create_user(username=username, email=email, password=password)

        default_group_name = "user"  # Change this to "bartender" if needed
        group = Group.objects.get(name=default_group_name)  # Get the group
        user.groups.add(group)  # Assign the user to the group

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


def export_cocktail_pdf(request, cocktail_id):
    """
    Generates a PDF file with the cocktail's details and serves it as a downloadable file.
    """
    cocktail = get_object_or_404(Cocktail, id=cocktail_id)
    ingredients = CocktailIngredient.objects.filter(cocktail=cocktail)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{cocktail.name}.pdf"'

    # Create PDF
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    y_position = height - 50

    # Title
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y_position, f"Cocktail: {cocktail.name}")
    y_position -= 30

    # Category & Alcoholic Status
    p.setFont("Helvetica", 12)
    p.drawString(50, y_position, f"Category: {cocktail.category.name if cocktail.category else 'Not Assigned'}")
    y_position -= 20

    alcohol_status = "Yes" if cocktail.is_alcoholic else "No"
    p.drawString(50, y_position, f"Alcoholic: {alcohol_status}")
    y_position -= 20

    # Add Classic/Customized Status
    cocktail_type = "Classic" if cocktail.is_classic else "Customized"
    p.drawString(50, y_position, f"Type: {cocktail_type}")
    y_position -= 30

    # Ingredients
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Ingredients:")
    y_position -= 20
    p.setFont("Helvetica", 12)

    for ingredient_entry in ingredients:
        p.drawString(60, y_position, f"- {ingredient_entry.ingredient.name}: {ingredient_entry.amount}")
        y_position -= 20

    # Instructions
    y_position -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Instructions:")
    y_position -= 20
    p.setFont("Helvetica", 12)
    p.drawString(60, y_position, cocktail.instructions)

    # Save PDF
    p.showPage()
    p.save()

    return response
