from django.urls import path
from .views import home,products,user_login,user_logout,user_register,product_details,add_products,seller_dashboard,delete_product,cart,add_to_cart,add_to_wishlist,wishlist
from .views import add_address,addresslist,edit_address,delete_address,payment_mode,order_success,payment_status,edit_profile,profile,change_password
from .views import password_reset,create_new_password,new_password,cod,delete_from_cart,delete_from_wishlist,myorder

urlpatterns = [
    path('',home,name="home"),

    #user paths
    path('profile/<int:user_id>/',profile,name="profile"),
    path('edit_profile/',edit_profile,name="edit_profile"),
    path('change_password/',change_password,name="change_password"),
    path('product/<slug:slug>/',product_details,name="product_details"),
    path('products/',products,name="products"),


    #seller_paths
    path('add_products/',add_products,name="add_products"),
    path('seller_dashboard',seller_dashboard,name="seller_dashboard"),
    path('delete_product/<int:product_id>',delete_product,name="delete_product"),


    #login,logout,register
    path('user_login/',user_login,name="user_login"),
    path('user_logout/',user_logout,name="user_logout"),
    path('user_register/',user_register,name='user_register'),


    #password_reset
    path('password_reset/',password_reset,name='password_reset'),
    path('create_new_password/<uuid:uuid>/<token>',create_new_password,name="create_new_password"),
    path('new_password/<int:user_id>',new_password,name="new_password"),


    #cart
    path('add_to_cart/<int:product_id>',add_to_cart, name="add_to_cart"),
    path('delete_from_cart/<int:product_id>',delete_from_cart,name="delete_from_cart"),
    path('cart/', cart, name="cart"),

    
    #wishlist
    path('add_to_wishlist/<int:product_id>', add_to_wishlist, name="add_to_wishlist"),
    path('delete_from_wishlist/<int:product_id>',delete_from_wishlist,name="delete_from_wishlist"),
    path('wishlist/', wishlist, name="wishlist"),

    
    #addresslist
    path('add_address/', add_address, name="add_address"),
    path('addresslist/', addresslist, name="addresslist"),
    path('edit_address/<int:address_id>', edit_address, name="edit_address"),
    path('delete_address/<int:address_id>', delete_address, name="delete_address"),


    #payment
    path('payment_mode/<int:address_id>',payment_mode,name='payment_mode'),
    path('cod/<str:order_id>',cod,name="cod"),
    path('order_success/',order_success,name="order_success"),
    path('webhook/',payment_status,name='payment_status'),


    #myorders
    path('myorder',myorder,name="myorder")
   
]