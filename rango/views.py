from django.http import HttpResponse
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
    return HttpResponse("Rango says hey there partner! <br/> <a href='/rango/about/'>About</a>")
    #category_list = Category.objects.order_by('-likes')[:5]
    #page_list = Page.objects.order_by('-views')[:5]

    #context_dict = {}
    #context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
    #context_dict['categories'] = category_list
    #context_dict['pages'] = page_list

    #visitor_cookie_handler(request)

    #response = render(request, 'rango/index.html', context=context_dict)
    #return response
    return render(request, 'rango/index.html')
    return HttpResponse("Rango says hey there partner!")

# A helper method
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val


def about(request):
    return HttpResponse("Rango says here is the about page. <br/> <a href='/rango/'>Index</a>")
    #visitor_cookie_handler(request)  # Ensure we update visit count
    #visits = request.session.get('visits', 1)  # Retrieve the visit count

    #context_dict = {
     #   'MEDIA_URL': settings.MEDIA_URL,
     #   'developer_name': 'Sam Lynch',
     #   'visits': visits,  # Pass visit count to the template
    #}

    #return render(request, 'rango/about.html', context=context_dict)
    return HttpResponse("Rango says here is the about page.")

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
# Chapter 7 wants ANYONE to add a category (no login).
# Chapter 9 wants to require login. We'll do the final version:
#   1) Check if user is authenticated; otherwise redirect to login.
#   2) If user POSTs a duplicate name, show "Category with this Name already exists."
# --------------------------------------------------

def add_category(request):
    # If user is not logged in, direct them to login.
    if not request.user.is_authenticated:
        return redirect(f"{reverse('rango:login')}?next=/rango/add_category/")

    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            # Check if a category with the same name already exists
            name = form.cleaned_data['name']
            if Category.objects.filter(name__iexact=name).exists():
                # Add an error to the form
                form.add_error('name', 'Category with this Name already exists.')
            else:
                form.save(commit=True)
                return redirect('rango:index')
        else:
            print(form.errors)

    return render(request, 'rango/add_category.html', {'form': form})


# --------------------------------------------------
# ADD PAGE
# Chapter 7 wants ANYONE to add a page. 
# Chapter 9 wants only logged-in users to add pages.
# We also must first check if category slug exists. 
# If no category => redirect /rango/
# If user not logged in => redirect /rango/login
# --------------------------------------------------

def add_page(request, category_name_slug):
    # 1) Check if category exists
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        # The Chapter 7 tests specifically check redirect to /rango/ if category doesn't exist
        return redirect('rango:index')

    # 2) Check if user is logged in
    if not request.user.is_authenticated:
        # For Chapter 9, redirect to login if not logged in
        return redirect(f"{reverse('rango:login')}?next=/rango/category/{category_name_slug}/add_page/")

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
# Chapter 9 requires two forms: UserForm + UserProfileForm
# Also show "Rango says: <strong>register here!</strong>" on GET,
# and "Rango says: <strong>thank you for registering!</strong>" on success
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
# Chapter 9 wants a custom user_login function
# On success => redirect to /rango/
# --------------------------------------------------

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                # The Chapter 9 test specifically wants a redirect to /rango/
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
# Chapter 9 wants user_logout => redirect /rango/
# If user not logged in, test expects redirect to login or index?
# We'll keep it simple: if not logged in, do same.
# --------------------------------------------------

def user_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('rango:index')
    else:
        # If user not logged in, we can just redirect them to login or index.
        # The test says it expects a 302 => login, but some versions want index.
        # We'll do the simpler approach: redirect to /rango/login
        return redirect('rango:login')


# --------------------------------------------------
# RESTRICTED
# Chapter 9 says restricted => login_required
# We'll do it in code, or manually check
# --------------------------------------------------

def restricted(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('rango:login')}?next=/rango/restricted/")
    return render(request, 'rango/restricted.html')