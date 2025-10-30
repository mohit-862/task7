from celery import shared_task
import os
from dotenv import load_dotenv
from app.models import Order
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

    send_mail(subject,body,sender,reciever,fail_silently=False)
    