from celery import shared_task
import os
from dotenv import load_dotenv
from app.models import Order,Customuser
from django.core.mail import send_mail


load_dotenv()
@shared_task
def confirmation_mail(order_id):
    obj = Order.objects.get(razorpay_order_id = order_id)
    subject = "Order Confirmation mail"
    body = f"""Order is placed Successfully.\nAn amount of {obj.total} is recieved. your order id is {obj.razorpay_order_id}.\n
                your payment ID is {obj.razorpay_payment_id} and order is shipped to {obj.shipping_address}.
                Thankyou {obj.user.get_full_name()}
                """
    sender = os.getenv('MAIL')
    reciever = [obj.user.email]   
    print("Mail sending")
    send_mail(subject,body,sender,reciever,fail_silently=False)
    print("mail send")
    
@shared_task
def password_reset_mail(user_id):
    obj = Customuser.objects.get(id = user_id)
    subject = "Password changed successfully"
    body = f"""password for profile {obj.username} is changed Successfully"""
    sender = os.getenv('MAIL')
    reciever = [obj.email]   
    print("Mail sending")
    send_mail(subject,body,sender,reciever,fail_silently=False)
    print("mail send")
