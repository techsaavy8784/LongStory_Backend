from django.shortcuts import render

# Create your views here.

from users.models import (
    User,
    Payment
)
from users.serializers import (
    UserInfoSerializer
)

from rest_framework.response import Response
from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from products.utils import convertToBoolean
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.template.loader import render_to_string

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  # Your webhook secret

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)

    # Handle payment_method.attached event
    if event.type == 'payment_method.attached':
        payment_method = event.data.object  # Payment Method object attached
        print("payment_method.attached")
    if event.type == 'customer.created':
        customer = event.data.object  # Payment Method object attached
        print("customer.created")
    if event.type == 'customer.updated':
        customer = event.data.object  # Payment Method object attached
        print("customer.updated")
    if event.type == 'customer.subscription.created':
        subscription = event.data.object  # Payment Method object attached
        print("customer.subscription.created")
    
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        # Handle the successful Payment Intent event here
        print(f"Payment Intent succeeded: {payment_intent.id}")
    if event.type == 'invoice.payment_failed':
        # Handle the payment failure event
        invoice = event.data.object
        print("invoice_failed", invoice)
        customer_id = invoice.customer
        if invoice.subscription is not None:
            subscription_id = invoice.subscription
            print(f"This invoice for subscription: {subscription_id} failed")
            # subscription = stripe.Subscription.retrieve(subscription_id)
            # stripe.Subscription.delete(subscription_id)

        else:
            print(f"This invoice is not for subscription")       
        
    if event.type == 'invoice.payment_succeeded':
        invoice = event.data.object
        if invoice.subscription is not None:
            print(f"This invoice for subscription: {invoice.subscription} succeeded")
            subject = 'Subscription done'
            context = {
                'email': invoice.customer_email,
                'username': invoice.customer_name,
                'amount_paid':invoice.amount_paid
            }
            message = render_to_string('order.html', context)

            send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [invoice.customer_email], fail_silently=False, html_message=message)
            customer_id = invoice.customer
    if event.type == 'charge.refunded':
        refund = event.data.object
        # Handle the successful refund event here
        print(f"Refund succeeded: {refund.id}")
        
    if event.type == "customer.subscription.deleted":
        subscription = event.data.object
        print("customer.subscription.deleted")
        # Handle the canceled subscription event
    if event.type == "customer.subscription.paused":
        subscription = event.data.object
        print("customer.subscription.paused")
        # Handle the canceled subscription event

    return HttpResponse(status=200)

        
def fc_create_and_confirm_payment_intent(payment_method_id, amount, currency,email, customer_id):
    result = {
        "success": False,
        "payment_intent": None,
        "invoice":None,
        "message": ""
    }
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # The amount in cents (e.g., $10.00)
            payment_method=payment_method_id,  # Specify the payment method ID
            confirm=True,  # Confirm the payment intent immediately
            currency=currency,
            receipt_email=email,
            customer=customer_id,
            automatic_payment_methods={
                'enabled': True,
                'allow_redirects': 'never',
            }
        )       
        
        result["payment_intent"] = intent
        
        # Handle the Payment Intent response as needed
        if intent.status == 'succeeded':
            result["success"] = True           
            
            result["message"] = "Payment succeeded"
        else:
            print("Payment not succeeded")
            result["success"] = False
            result["message"] = "Payment not succeeded"

    except stripe.error.StripeError as e:
        # Handle Stripe API errors
        print("Stripe API Error:", str(e))
        result["message"] = str(e)
        
    return result

def fc_create_refund(payment_intent_id):
    result = {
        "success": False,
        "refund": None,
        "message": ""
    }
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if payment_intent.latest_charge:
            # Get the charge ID
            charge_id = payment_intent.latest_charge
            refund = stripe.Refund.create(charge=charge_id)
            print(refund)
            result["success"] = True
            result["refund"] = refund
    except stripe.error.StripeError as e:
        # Handle Stripe API errors, e.g., display an error message
        result["message"] = str(e)
        
    return result

def fc_create_and_attach_payment_method(type, token_id, customer_id):
    result = {
        "success": False,
        "payment_method": None,
        "message": ""
    }
    try:
        payment_method = None
        if type == "card":
            payment_method = stripe.PaymentMethod.create(
                type='card',
                card={'token': token_id},
            )
        else:
            payment_method = stripe.PaymentMethod.create(
                type='ach_debit',
                ach_debit={'token': token_id},
            )
        stripe.PaymentMethod.attach(
            payment_method.id,
            customer=customer_id  # Replace with the customer's ID
        )
        result["success"] = True
        result["payment_method"] = payment_method
    except stripe.error.StripeError as e:
        # Handle Stripe API errors, e.g., display an error message
        result["message"] = str(e)
        
    return result

def fc_delete_payment_method(payment_method_id):
    result = {
        "success": False,
        "message": ""
    }
    try:        
        stripe.PaymentMethod.detach(payment_method_id)
        result["success"] = True        
    except stripe.error.StripeError as e:
        # Handle Stripe API errors, e.g., display an error message
        result["message"] = str(e)
        
    return result

def fc_create_payment_model(new_payment_method, user):
    result = {
        "success": False,
        "payment": None,
        "message": ""
    }
    try:
        if new_payment_method.type == "card":
            payment = Payment.objects.create(
                user=user,
                stripe_payment_method_id=new_payment_method.id,
                type = new_payment_method.type,
                brand = new_payment_method.card.brand,
                last4 = new_payment_method.card.last4,
                country = new_payment_method.card.country
            )
        elif new_payment_method.type == "ach_debit":
            payment = Payment.objects.create(
                user=user,
                stripe_payment_method_id=new_payment_method.id,
                type = new_payment_method.type,
                bank_name = new_payment_method.ach_debit.bank_name,
                last4 = new_payment_method.ach_debit.last4,
                country = new_payment_method.ach_debit.country,
                name = new_payment_method.billing_details.name,
                email = new_payment_method.billing_details.email,
            )       
        result["success"] = True
        result["payment"] = payment
    except:
        result["message"] = "faile to create payment model"
        
    return result
        

def fc_create_customer(user):
    result = {
        "success": False,
        "customer_id": None,
        "message": ""
    }
    try:
        stripe_customer = stripe.Customer.create(
            name=user.username,
            email=user.email,
        )
        result["success"] = True
        result["customer_id"] = stripe_customer.id
    except stripe.error.StripeError as e:
        # Handle Stripe API errors, e.g., display an error message
        result["message"] = str(e)
        
    return result

def fc_attach_payment_method_to_customer(customer_id, payment_method_id):
    result = {
        "success": False,
        "message": ""
    }
    try:
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id  # Replace with the customer's ID
        )
        result["success"] = True
    except stripe.error.StripeError as e:        
        result["message"] = str(e)
        
    return result

def fc_modify_default_payment_method(customer_id, payment_method_id):
    result = {
        "success": False,
        "message": ""
    }
    try:
        stripe.Customer.modify(
            customer_id,
            invoice_settings={
                'default_payment_method': payment_method_id
            }
        )
        result["success"] = True
    except stripe.error.StripeError as e:        
        result["message"] = str(e)
        
    return result

def fc_create_subscription_with_invoice(customer_id, payment_method_id):
    result = {
        "success": False,
        "subscription_id": None,
        "message": ""
    }
    try:
        stripe_subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': settings.STRIPE_PRICE_ID}],
            default_payment_method=payment_method_id,
            expand=["latest_invoice.payment_intent"]
        )
        result["success"] = True     
        result["subscription_id"] = stripe_subscription.id       
    
    except stripe.error.StripeError as e:        
        result["message"] = str(e)
        
    return result

def fc_update_subscription_payment_method(subscription_id, new_payment_method_id):
    result = {
        "success": False,
        "subscription_id": None,
        "message": ""
    }
    try:
        subscription = stripe.Subscription.modify(
            subscription_id,
            default_payment_method=new_payment_method_id
        )
        result["success"] = True     
        result["subscription_id"] = subscription.id  
    except stripe.error.StripeError as e:        
        result["message"] = str(e)
            

    return result

def fc_cancel_subscription(subscription_id):
    result = {
        "success": False,
        "message": ""
    }
    try:
        subscription = stripe.Subscription.delete(subscription_id)
        result["success"] = True    
    except stripe.error.StripeError as e:        
        result["message"] = str(e)
            

    return result

def fc_cancel_subscription_at_period_end(subscription_id):
    result = {
        "success": False,
        "message": ""
    }
    try:
        # Retrieve the subscription
        subscription = stripe.Subscription.retrieve(
            subscription_id,
        )
        # Update the subscription's billing cycle end
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )
        result["success"] = True    
    except stripe.error.StripeError as e:        
        result["message"] = str(e)            

    return result

def fc_resume_subscription(subscription_id):
    result = {
        "success": False,
        "message": ""
    }
    try:
        stripe.Subscription.resume(
            subscription_id,
            billing_cycle_anchor="now",
        )
        result["success"] = True    
    except stripe.error.StripeError as e:        
        result["message"] = str(e)            

    return result
        


class SubscriptionCreate(APIView):
    permission_classes = (IsAuthenticated, ) 
    
    def post(self, request):
        user = request.user
        payment_method_id = request.data.get("payment_method_id")
        new_payment_method = None
        type = request.data.get("type")
        token_id = request.data.get("token_id")
        if payment_method_id is None and (type is None or token_id is None):
            return Response(
                {
                    "error": "Payment Method id required"
                }, status=status.HTTP_400_BAD_REQUEST
            )
                 
        
        stripe_customer_id = user.stripe_customer_id
        stripe_subscription_id = user.stripe_subscription_id
        #create customer if there is no
        if stripe_customer_id is None:
            create_customer = fc_create_customer(user)
            if create_customer["success"] is True:
                user.stripe_customer_id = create_customer["customer_id"]
            else:
                return Response(
                    {
                        "error": create_customer["message"]
                    }, status=status.HTTP_400_BAD_REQUEST
                )                 
        if payment_method_id is None:
            if type is not None and token_id is not None:
                create_payment_method = fc_create_and_attach_payment_method(type, token_id, user.stripe_customer_id)
                if create_payment_method["success"] is True:
                    payment_method_id = create_payment_method["payment_method"].id
                    new_payment_method = create_payment_method["payment_method"]
                else:
                    return Response(
                    {
                        "error": create_payment_method["message"]
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {
                        "error": "Payment Method id or token_id and type required"
                    }, status=status.HTTP_400_BAD_REQUEST
                )       
        # create subscription if there is no
        if stripe_subscription_id is None:            
            create_subscription = fc_create_subscription_with_invoice(user.stripe_customer_id, payment_method_id)
            if create_subscription["success"] is True:
                user.stripe_subscription_id = create_subscription["subscription_id"]
            else:
                return Response(
                    {
                        "error": create_subscription["message"]
                    }, status=status.HTTP_400_BAD_REQUEST
                )        
            
        # update default payment method for subscription
        if stripe_subscription_id is not None and stripe_customer_id is not None:
            
            update_subscription_payment_method = fc_update_subscription_payment_method(stripe_subscription_id, payment_method_id)
            if update_subscription_payment_method["success"] is False:
                return Response(
                    {
                        "error": update_subscription_payment_method["message"]
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        # create payment model instance if new payment method created
        if new_payment_method is not None:
            create_payment_model = fc_create_payment_model(new_payment_method, user)
            if create_payment_model["success"] is False:
                return Response(
                    {
                        "error": create_payment_model["message"]
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        # user.auth_status = 9
        user.save()
        return Response({
                'user': UserInfoSerializer(user).data,
                'message': 'User was updated successfully'
            },status=status.HTTP_200_OK
        )  

