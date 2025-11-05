from django.shortcuts import render,redirect
from django.http import HttpResponse,JsonResponse,HttpResponseBadRequest
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import json
from django.contrib.auth.tokens import PasswordResetTokenGenerator




import razorpay
import os

# Create your views here.
from task import settings
from task.settings import BASE_DIR
from .models import Customuser,Category,Product,Cart, Wishlist, Addresslist,Order,Myorder
from app.task import confirmation_mail,password_changed_mail,password_reset_mail
from app.decorators import seller_required,user_required




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
        profile_image = request.FILES.get('profile_image',None)
        email = request.POST['email']
        password = request.POST['password']
        phone = request.POST['phone']
        role  = request.POST['role']
        print(role)

        user = Customuser(first_name=fname.capitalize(),last_name=lname.capitalize(),username=username,email=email,phone=phone,role=role,profile_image=profile_image)
        user.set_password(password)
        if role == "seller":
            user.is_staff = True
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

#---------------------------------------Profile pages(for user and seller both)---------------------------------------------------------------------------


@login_required(login_url="user_login")
def profile(request,user_id):
    user = Customuser.objects.get(id = user_id)
    return render(request,'app/profile.html',{'user':user})



@login_required(login_url="user_login")
def edit_profile(request):
    user = Customuser.objects.get(id = request.user.id)
    print(user.profile_image.url,"----------------------------------------------------------")
    if request.method == "POST":
        fname = request.POST['fname']
        lname = request.POST['lname']
        username = request.POST['username']
        email = request.POST['email']
        phone = request.POST['phone']
        profile_image = request.FILES.get('profile_image',None)


        user.first_name = fname
        user.last_name = lname
        user.username = username
        user.email = email
        user.phone = phone
        user.profile_image = profile_image
        user.save()
        messages.success(request, "profile updated successfully!")
        return redirect('profile')
    return render(request,'app/edit_profile.html',{'user':user})


def password_reset(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        try:
            user = Customuser.objects.get(username = username,email = email)
            print(user)
        except Customuser.DoesNotExist:
            messages.success(request,"username or email does not exist")
            return redirect('password_reset')
        
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        password_reset_mail.delay(user.username,user.email,user.uuid,token)
        messages.add_message(request,messages.INFO,"A password reset mail has been sent to your registered email")
        return redirect('home')
    return render(request,'app/password_reset.html')


def create_new_password(request,uuid,token):
    try:
        user = Customuser.objects.get(uuid = uuid)
    except:
        print("===user is not found from uuid")

    token_generator = PasswordResetTokenGenerator()
    result = token_generator.check_token(user,token)

    if not result:
        messages.add_message(request,messages.INFO,"token is not verified or the link is expired")
        return redirect("home")
    
    return render(request,'app/new_password.html',{'user':user})


def new_password(request,user_id):
    user = Customuser.objects.get(id = user_id)
    if request.method == 'POST':
        npassword = request.POST['npassword']
        cpassword = request.POST['cpassword']
        has_uppercase = False
        has_lowercase = False
        has_digit = False
        has_special = False

        if not npassword == cpassword:
            messages.add_message(request,messages.INFO,"Both password field should be equal")
            return redirect('change_password')
        if (len(npassword) < 8 and len(npassword) > 20) and " " in npassword:
            messages.add_message(request,messages.INFO,"Password should be 8 - 20 characters long and not have space")
            return redirect('change_password')
        
        for ch in npassword:
            if not has_uppercase and 65<=ord(ch)<=90:
                has_uppercase = True
            elif not has_lowercase and 97<=ord(ch)<=122:
                has_lowercase = True
            elif not has_digit and 48<=ord(ch)<=57:
                has_digit = True
            elif not has_special and ch in {'@','_','#','-'}:
                has_special = True
            
        if not has_uppercase:
            messages.add_message(request,messages.INFO,"Password should have a uppercase character")
            return redirect('change_password')
        if not has_lowercase:
            messages.add_message(request,messages.INFO,"Password should have a lowercase character")
            return redirect('change_password')
        if not has_digit:
            messages.add_message(request,messages.INFO,"Password should have a digit")
            return redirect('change_password')
        if not has_special:
            messages.add_message(request,messages.INFO,"Password should have a special character {'@','_','#','-'}")
            return redirect('change_password')
        else:
            user.set_password(npassword)
            password_changed_mail.delay(user.id)
            user.save()
            messages.add_message(request,messages.INFO,"Password changed successfully")
    return redirect('user_login')
    


@login_required(login_url="user_login")
def change_password(request):
    user = Customuser.objects.get(id = request.user.id)
    if request.method == 'POST':
        current_password = request.POST['current_password']
        npassword = request.POST['npassword']
        cpassword = request.POST['cpassword']
        has_uppercase = False
        has_lowercase = False
        has_digit = False
        has_special = False


        if not user.check_password(current_password):
            messages.add_message(request,messages.INFO,"the current password is incorrect")
            return redirect('change_password')
        if not npassword == cpassword:
            messages.add_message(request,messages.INFO,"Both password field should be equal")
            return redirect('change_password')
        if (len(npassword) < 8 and len(npassword) > 20) and " " in npassword:
            messages.add_message(request,messages.INFO,"Password should be 8 - 20 characters long and not have space")
            return redirect('change_password')
        
        for ch in npassword:
            if not has_uppercase and 65<=ord(ch)<=90:
                has_uppercase = True
            elif not has_lowercase and 97<=ord(ch)<=122:
                has_lowercase = True
            elif not has_digit and 48<=ord(ch)<=57:
                has_digit = True
            elif not has_special and ch in {'@','_','#','-'}:
                has_special = True
            
        if not has_uppercase:
            messages.add_message(request,messages.INFO,"Password should have a uppercase character")
            return redirect('change_password')
        if not has_lowercase:
            messages.add_message(request,messages.INFO,"Password should have a lowercase character")
            return redirect('change_password')
        if not has_digit:
            messages.add_message(request,messages.INFO,"Password should have a digit")
            return redirect('change_password')
        if not has_special:
            messages.add_message(request,messages.INFO,"Password should have a special character")
            return redirect('change_password')
        else:
            user.set_password(npassword)
            password_changed_mail.delay(user.id)
            user.save()
            messages.add_message(request,messages.INFO,"Password changed successfully")
            logout(request)
            return redirect('user_login')
    return render(request,'app/change_password.html',{'user':user})



# ----------------------------------------user-------------------------------------------------


@user_required
@login_required(login_url="user_login")
def product_details(request,slug):
    product = Product.objects.get(slug = slug)
    context = {
        'product' : product
    }
    return render(request,'app/product_details.html',context)




@user_required
@login_required(login_url="user_login")
def products(request):
    categories = Category.objects.all() 
    products = Product.objects.all().order_by('id')

    query = request.GET.get('search', "")
    order = request.GET.get('filter', "")
    category = request.GET.get('category', "")

    if query:
        products = products.filter(title__contains=query).order_by('id')
    if category:
        products = products.filter(category_id=category).order_by('id')
    if order == 'asc':
        products = products.order_by('price')
    elif order == 'desc':
        products = products.order_by('-price')

    paginator = Paginator(products,5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)          
    return render(request,'app/products.html',{'page_obj':page_obj,'categories':categories})
            


# -----------------------------selller------------------------------------------------------------------------------------


@seller_required
@login_required(login_url="user_login")
def seller_dashboard(request):
    context = all_products()
    paginator = Paginator(context['products'],5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context.update({'page_obj':page_obj})
    return render(request,'app/seller_dashboard.html',context)


@seller_required
@login_required(login_url="user_login")
def add_products(request):
    context = all_category()
    role = request.session['role']
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
    return render(request,'app/add_products.html',context)
    



@seller_required
@login_required(login_url="user_login")
def delete_product(request,product_id):
    user = request.session['name']
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
        

# ---------------------------------------------cart--------------------------------------------------------------------


@user_required
@login_required(login_url='user_login')
def add_to_cart(request, product_id):
    product = Product.objects.get(id = product_id)
    cart_item,created = Cart.objects.get_or_create(user=request.user , product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    messages.add_message(request,messages.INFO,f"{product.title} added to cart!")
    return redirect('products')


@user_required
@login_required(login_url='user_login')
def delete_from_cart(request, product_id):
    cart_item = Cart.objects.get(user=request.user , product_id = product_id)
    cart_item.delete()
    messages.add_message(request,messages.INFO,f"item removed from cart!")
    return redirect('cart')





@user_required
@login_required(login_url='user_login')
def cart(request):
    cart_items = Cart.objects.filter(user_id = request.user.id)
    total = 0
    for items in cart_items:
        total += items.product.price * items.quantity  
    request.session['total'] = str(total)      
    return render(request, 'app/cart.html', {'cart_items': cart_items, 'total': total})


# ---------------------------------------------whishlist--------------------------------------------------------------------

@user_required
@login_required(login_url='user_login')
def add_to_wishlist(request, product_id):
    product = Product.objects.get(id=product_id)
    wishlist,created =  Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.add_message(request,messages.INFO,f"{product.title} added to wishlist!")
    else:
        messages.add_message(request,messages.INFO,f"{product.title} is already in wishlist!")    
    return redirect('products')



@user_required
@login_required(login_url='user_login')
def delete_from_wishlist(request, product_id):
    wishlist_item = Wishlist.objects.get(user = request.user , product_id = product_id)
    wishlist_item.delete()
    messages.add_message(request,messages.INFO,f"item removed from wishlist!")
    return redirect('wishlist')




@login_required(login_url='user_login')
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user_id=request.user.id)
    return render(request, 'app/wishlist.html', {'wishlist_items': wishlist_items})




# ---------------------------------------------addresslist--------------------------------------------------------------------



@user_required
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
@user_required
def addresslist(request):
    addresslist = Addresslist.objects.filter(user_id = request.user.id)
    return render(request, 'app/addresslist.html', {'addresslist': addresslist})




@user_required
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


@user_required
@login_required(login_url='user_login')
def delete_address(request, address_id):
    address = Addresslist.objects.get(id=address_id)
    address.delete()
    messages.add_message(request,messages.INFO,"Address deleted successfully!!!")
    return redirect('addresslist')





#------------------------------------myorder-----------------------------------------------------



def myorder(request):
    return redirect(request,'app/myorder.html')




# def cart_to_myorder(order_id):
#     order_obj = Order.objects.get(razorpay_order_id = order_id)
#     print(order_obj.user)
#     try:
#         myorder = Myorder.objects.create(user = order_obj.user, order = order_obj)
#         cart_items= Cart.objects.filter(user = order_obj.user)
#         for item in cart_items:
#             myorder.product.add()




#     except:
#         print("Myorder is not created ======================================================")



# ---------------------------------------payment ----------------------------------------------------

client = razorpay.Client(auth=(settings.KEY, settings.SECRET_KEY))


@csrf_exempt
def payment_mode(request,address_id):
    print("---------payment mode---------------------------------------------")
    try:
        address= Addresslist.objects.get(id=address_id)
    except:
        return redirect('cart')
    request.session['address'] = f"{address.address} {address.city} {address.state} {address.pincode}"
    total = float(request.session.get('total',500))
    address = request.session.get('address')
    print(total)
    print(address)
    data = { "amount": total*100, "currency": "INR",'payment_capture': 1 }

    try:
        obj,created = Order.objects.get_or_create(user = request.user,total=total,shipping_address = address,pay_status='Pending')
    except:
        messages.add_message(request,messages.INFO,'you have more than one pending order with the same order try again after changing the details')
        return redirect('cart')

    if created:
        payment = client.order.create(data=data)
        obj.pay_status = 'Pending'
        obj.razorpay_order_id = payment['id']
        obj.save()


    context = {'order_id':obj.razorpay_order_id,'user':request.user,'total':total,'razor_pay_key_id':settings.KEY}
    return render(request,'app/payment_mode.html',context)




def cod(request,order_id):
    print(order_id)
    obj = Order.objects.get(razorpay_order_id = order_id)
    print(obj)
    obj.pay_mode = "Cash on Delivery"
    obj.pay_status = "Success"
    obj.save()
    # cart_to_myorder(order_id)
    return render(request,'app/order_success.html')



def handle_payment_success(data):
    print("===============payment success-===============")
    order_id = data['payload']['payment']['entity']['order_id']
    print(order_id)
    obj = Order.objects.get(razorpay_order_id = order_id)
    print(obj)
    print(obj.user)
    print(obj.shipping_address)
    obj.razorpay_payment_id = data['payload']['payment']['entity']['id']
    obj.pay_status = "Success"
    obj.pay_mode = data['payload']['payment']['entity']['method']
    obj.save()
    # confirmation_mail.delay(order_id) 
    # cart_to_myorder(order_id)
    # # messages.add_message(request,messages.INFO,'Payment is succeded')
    print("===============payment success-===============")




def handle_payment_failure(data):
    print("===============payment failed-===============")
    order_id = data['payload']['payment']['entity']['order_id']
    obj = Order.objects.get(razorpay_order_id = order_id)
    print(obj)
    print(obj.user)
    print(obj.shipping_address)
    obj.razorpay_payment_id = data['payload']['payment']['entity']['id']
    obj.pay_status = "Failed"
    obj.pay_mode = data['payload']['payment']['entity']['method']
    obj.failure_reason = data['payload']['payment']['entity']['error_reason']
    obj.failure_description = data['payload']['payment']['entity']['error_description']
    obj.save()
    print("===============payment failed-===============")





@csrf_exempt
def order_success(request):
    print("============order_suiccess=====================")
    if request.method == 'POST':
        order_id = request.POST.get('razorpay_order_id',None)
        print(order_id)
        
        if order_id is not None:  
            payment_id = request.POST['razorpay_payment_id']
            print(payment_id)
            signature = request.POST['razorpay_signature']
            print(signature)
            client = razorpay.Client(auth=(settings.KEY, settings.SECRET_KEY))
            data = {
                'razorpay_order_id' :order_id,
                'razorpay_payment_id':payment_id,
                'razorpay_signature':signature
            }
            
            client.utility.verify_payment_signature(data)
            obj = Order.objects.get(razorpay_order_id = order_id)
            print(obj)
            print(obj.user)
            print(obj.shipping_address)
            obj.razorpay_payment_id = payment_id
            obj.payment_status = "Success"
            obj.save()
            messages.add_message(request,messages.INFO,'Payment is succeded')
        else:   
            messages.add_message(request,messages.INFO,'Payment fails try again!!')
            return redirect('cart')
        print("===============order success ===============================================")
    return render(request,'app/order_success.html')




@csrf_exempt
def payment_status(request):
    print("=====++++++++++==payment status=======================================")
    if request.method == "POST":
        print("------------1-------------------")
        try:
            print("--------2-------------")
            data = json.loads(request.body)
        except json.JSONDecodeError:
            print("--------------3----------")
            return HttpResponseBadRequest("Invalid JSON payload.")
        print("------4-------------------")
        print(data)
        print("webhuuuuuuuuuuuuok activated")
        


        event = data.get("event")
        print(event)

        if event == "payment.captured":
            handle_payment_success(data)
        elif event== "payment.failed":
            handle_payment_failure(data)
        else:
            return HttpResponseBadRequest("Unhandled event")
    print("=======payment status=======================================")
    return JsonResponse({'status':200})
        

