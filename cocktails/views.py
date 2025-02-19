from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required

from .models import Cocktail, User
from .utils import check_pasword
from .forms import ProfileUpdateForm, UserUpdateForm


def index(request):
    return render(request, 'index.html')


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
    paginator = Paginator(cocktails, 8)  # Show 8 cocktails per page
    page_number = request.GET.get("page")
    paged_cocktails = paginator.get_page(page_number)

    context = {"cocktails": paged_cocktails}
    return render(request, "cocktail_list.html", context)


def cocktail_detail(request, cocktail_id):
    """
    View to display detailed information about a single classic cocktail.
    """
    cocktail = get_object_or_404(Cocktail, id=cocktail_id, is_classic=True)

    context = {"cocktail": cocktail}
    return render(request, "cocktail_detail.html", context)


@csrf_protect
def register_user(request):
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
