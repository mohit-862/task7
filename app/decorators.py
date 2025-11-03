from django.shortcuts import redirect
from django.contrib import messages


def seller_required(view_func):
    def wrapper(request,*args,**kwargs):
        if request.user.role == 'seller':
            return view_func(request,*args,**kwargs)
        else:
            messages.add_message(request,messages.INFO,f"Invalid user needs a seller role to access the page")
            return redirect('user_login')
    return wrapper


def user_required(view_func):
    def wrapper(request,*args,**kwargs):
        if request.user.role == 'user':
            return view_func(request,*args,**kwargs)
        else:
            messages.add_message(request,messages.INFO,f"Invalid user needs a user role to access the page")
            return redirect('user_login')
    return wrapper


