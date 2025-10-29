from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from task.settings import BASE_DIR
import os

# Create your views here.
from .models import Customuser,Category,Product,Cart, Wishlist, Addresslist




ROLES = ['seller','user']

def all_category():
    categories = Category.objects.all()
    context = {
        'categories' : categories
    }
    return context

def all_products():
    products = Product.objects.all()
    context = {
        'products' : products
    }
    return context



def home(request):
    return render(request,'app/home.html')


# login , logout  ,register

def user_register(request):
    if request.method == 'POST':
        fname = request.POST['fname']
        lname = request.POST['lname']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        phone = request.POST['phone']
        role  = request.POST['role']
        print(role)

        user = Customuser(first_name=fname.capitalize(),last_name=lname.capitalize(),username=username,email=email,phone=phone,role=role)
        user.set_password(password)
        try:
            user.save()
        except Exception as e:
            print(e)
            messages.add_message(request,messages.INFO,"User cannot be registered")
            return redirect('user_register')
        return redirect('user_login')
    return render(request,'app/register.html',{'roles':ROLES})


def user_login(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            request.session['role'] = user.role
            if user.role == 'seller':
                return redirect('seller_dashboard')
            else:
                return redirect('products')
        else:
            messages.add_message(request,messages.INFO,"INVALID Credentials try login again !!!")
            return redirect("user_login")
    return render(request,'app/login.html')


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect("home")

#---------------------------------------user---------------------------------------------------------------------------

def product_details(request,slug):
    product = Product.objects.get(slug = slug)
    context = {
        'product' : product
    }
    return render(request,'app/product_details.html',context)




@login_required(login_url="user_login")
def products(request):
    role = request.session['role']
    if role != 'user':
        messages.add_message(request,messages.INFO,f"Invalid user needs a user role to access the page")
        return redirect("user_login")
    
    categories = Category.objects.all() 
    products = Product.objects.all()

    query = request.GET.get('search', "")
    order = request.GET.get('filter', "")
    category = request.GET.get('category', "")

    if query:
        products = products.filter(title__contains=query)
    if category:
        products = products.filter(category_id=category)
    if order == 'asc':
        products = products.order_by('price')
    elif order == 'desc':
        products = products.order_by('-price')

    paginator = Paginator(products,5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)          
    return render(request,'app/products.html',{'page_obj':page_obj,'categories':categories})
            


# -----------------------------selller------------------------------------------------------------------------------------


@login_required(login_url="user_login")
def seller_dashboard(request):
    role = request.session['role']
    if role == 'seller':
        context = all_products()
        paginator = Paginator(context['products'],5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context.update({'page_obj':page_obj})
        return render(request,'app/seller_dashboard.html',context)
    else:
        messages.add_message(request,messages.INFO,f"Invalid user needs a seller role to access the page")
        return redirect("user_login")


@login_required(login_url="user_login")
def add_products(request):
    context = all_category()
    role = request.session['role']
    if request.method == 'GET' and role == 'seller':
        return render(request,'app/add_products.html',context)
    if request.method == "POST":
        title = request.POST['title']
        description = request.POST['description']
        product_img = request.FILES["image"]
        price  = request.POST['price']
        category = request.POST['category']
        cat = Category.objects.get(id = category)
        print(title,description,product_img,price,category)
        try:
            Product.objects.create(title=title,description=description,product_img=product_img,price=price,category=cat)
            messages.add_message(request,messages.INFO,'Product added successfully')
        except Exception as e:
            print(e)
            messages.add_message(request,messages.INFO,'Product might already exist')
        return redirect("add_products")
    



@login_required(login_url="user_login")
def delete_product(request,product_id):
    role = request.session['role']
    user = request.session['name']
    if role == 'seller':
        obj = Product.objects.get(id = product_id)
        context = all_products()
        paginator = Paginator(context['products'],5)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context.update({'page_obj':page_obj,'user': user})
        img_path = obj.product_img.path
        try:
            os.remove(img_path)
            obj.delete()
            messages.add_message(request,messages.INFO,"Product deleted successfully")
        except FileNotFoundError:
            messages.add_message(request,messages.INFO,"Product is not found")
        except:
            messages.add_message(request,messages.INFO,"Product is not deleted")
       
        return render(request,'app/seller_dashboard.html',context)
    else:
        messages.add_message(request,messages.INFO,f"Invalid user needs a seller role to access the page")
        return redirect("user_login")
    



    


# ---------------------------------------------cart--------------------------------------------------------------------


@login_required(login_url='user_login')
def add_to_cart(request, product_id):
    product = Product.objects.get(id = product_id)
    cart_item,created = Cart.objects.get_or_create(user=request.user , product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    messages.add_message(request,messages.INFO,f"{product.title} added to cart!")
    return redirect('cart')


@login_required(login_url='user_login')
def cart(request):
    cart_items = Cart.objects.filter(user_id = request.user.id)
    total = 0
    for items in cart_items:
        total += items.product.price * items.quantity        
    return render(request, 'app/cart.html', {'cart_items': cart_items, 'total': total})


# ---------------------------------------------whishlist--------------------------------------------------------------------

@login_required(login_url='user_login')
def add_to_wishlist(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        Wishlist.objects.create(user=request.user, product=product)
        messages.add_message(request,messages.INFO,f"{product.title} added to wishlist!")
    except:
        messages.add_message(request,messages.INFO,f"{product.title} cannot be added to wishlist!")    
    return redirect('wishlist')


@login_required(login_url='user_login')
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user_id=request.user.id)
    return render(request, 'app/wishlist.html', {'wishlist_items': wishlist_items})


# ---------------------------------------------addresslist--------------------------------------------------------------------


@login_required(login_url='user_login')
def add_address(request):
    if request.method == 'POST':
        user = request.user
        address = request.POST['address']
        city = request.POST['city']
        state = request.POST['state']
        pincode = request.POST['pincode']
        Addresslist.objects.create(user=user,address=address,city=city,state=state,pincode=pincode)
        messages.add_message(request,messages.INFO,"Address added successfully!!!")
        return redirect('addresslist')
    return render(request, 'app/add_address.html')



@login_required(login_url='user_login')
def addresslist(request):
    addresslist = Addresslist.objects.filter(user_id = request.user.id)
    return render(request, 'app/addresslist.html', {'addresslist': addresslist})




@login_required(login_url='user_login')
def edit_address(request, address_id):
    address = Addresslist.objects.get(id=address_id)
    if request.method == 'POST':
        address.address = request.POST['address']
        address.city = request.POST['city']
        address.state = request.POST['state']
        address.pincode = request.POST['pincode']
        address.save()
        messages.success(request, "Address updated successfully!")
        return redirect('addresslist')
    return render(request, 'app/edit_address.html', {'address': address})


@login_required(login_url='user_login')
def delete_address(request, address_id):
    address = Addresslist.objects.get(id=address_id)
    address.delete()
    messages.add_message(request,messages.INFO,"Address deleted successfully!!!")
    return redirect('addresslist')