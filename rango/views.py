from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static



def index(request):
    context_dict = {'boldmessage': "Crunchy, creamy, cookie, candy, cupcake!"}
    return render(request, 'rango/index.html', context=context_dict)

def about(request):
    context_dict = {'MEDIA_URL': settings.MEDIA_URL, 'developer_name': 'Sam Lynch'}
    return render(request, 'rango/about.html', context=context_dict)

