from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from datetime import datetime

from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm

# --------------------------------------------------
# INDEX AND ABOUT
# --------------------------------------------------

def index(request):
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {}
    context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
    context_dict['categories'] = category_list
    context_dict['pages'] = page_list

    visitor_cookie_handler(request)

    response = render(request, 'rango/index.html', context=context_dict)
    return response


def about(request):
    visitor_cookie_handler(request)  # Ensure we update visit count
    visits = request.session.get('visits', 1)  # Retrieve the visit count

    context_dict = {
        'MEDIA_URL': settings.MEDIA_URL,
        'developer_name': 'Sam Lynch',
        'visits': visits,  # Pass visit count to the template
    }

    return render(request, 'rango/about.html', context=context_dict)


def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))
    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).days > 0:
        visits += 1
        request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = last_visit_cookie

    request.session['visits'] = visits


# --------------------------------------------------
# SHOW CATEGORY
# --------------------------------------------------

def show_category(request, category_name_slug):
    context_dict = {}
    try:
        category = Category.objects.get(slug=category_name_slug)
        pages = Page.objects.filter(category=category)
        context_dict['category'] = category
        context_dict['pages'] = pages
    except Category.DoesNotExist:
        # If no category is found, set both to None.
        context_dict['category'] = None
        context_dict['pages'] = None

    return render(request, 'rango/category.html', context=context_dict)


# --------------------------------------------------
# ADD CATEGORY
# Chapter 7: ANYONE can add a category
# (Remove the Chapter 9 login check so the tests pass.)
# --------------------------------------------------

def add_category(request):
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            # If a category with same name already exists
            if Category.objects.filter(name__iexact=name).exists():
                form.add_error('name', 'Category with this Name already exists.')
            else:
                form.save(commit=True)
                return redirect('rango:index')
        else:
            print(form.errors)

    return render(request, 'rango/add_category.html', {'form': form})


# --------------------------------------------------
# ADD PAGE
# Chapter 7: ANYONE can add a page
# (Remove the Chapter 9 login check so the tests pass.)
# --------------------------------------------------

def add_page(request, category_name_slug):
    # 1) Check if category exists
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        return redirect('rango:index')

    form = PageForm()

    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            page = form.save(commit=False)
            page.category = category
            page.views = 0
            page.save()
            return redirect(reverse('rango:show_category',
                                    kwargs={'category_name_slug': category_name_slug}))
        else:
            print(form.errors)

    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context=context_dict)


# --------------------------------------------------
# REGISTER
# Chapter 9 code, can remain for now.
# --------------------------------------------------

def register(request):
    registered = False

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            profile.save()

            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request,
                  'rango/register.html',
                  {'user_form': user_form,
                   'profile_form': profile_form,
                   'registered': registered})


# --------------------------------------------------
# LOGIN
# Chapter 9 code, can remain for now.
# --------------------------------------------------

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return redirect('rango:index')
            else:
                return render(request, 'rango/login.html',
                              {'error_message': "Your account is disabled."})
        else:
            return render(request, 'rango/login.html',
                          {'error_message': "Invalid login details."})

    # GET request
    return render(request, 'rango/login.html')


# --------------------------------------------------
# LOGOUT
# Chapter 9 code, can remain for now.
# --------------------------------------------------

def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('rango:index')
    else:
        return redirect('rango:login')


# --------------------------------------------------
# RESTRICTED
# Chapter 9 code, can remain for now.
# --------------------------------------------------

def restricted(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('rango:login')}?next=/rango/restricted/")
    return render(request, 'rango/restricted.html')
