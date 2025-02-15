from django.urls import path
from rango import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'rango'

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('category/<slug:category_name_slug>/', views.show_category, name='show_category'),
    path('category/<slug:category_name_slug>/add_page/', views.add_page, name='add_page'),
    path('add_category/', views.add_category, name='add_category'),
    # CUSTOM login/logout from Chapter 9:
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    # Registration
    path('register/', views.register, name='register'),
    # Restricted page
    path('restricted/', views.restricted, name='restricted'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
