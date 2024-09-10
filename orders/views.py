from django.shortcuts import render

# Create your views here.
from orders.models import (
    OrderDetail,
    OrderItem
)

from orders.serializers import (
    OrderItemSerializer,
    OrderDetailSerializer
)

from products.models import (
    Product
)

from users.models import (
    User,
    Address,
    Payment
)

from products.serializers import (
    ProductSerializer
)

from users.serializers import (
    UserMainInfoSerializer,
    AddressSerializer,
    PaymentSerializer
)

from rest_framework.response import Response
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from products.utils import convertToBoolean
from payments.views import (
    fc_create_and_confirm_payment_intent
)
from orders.utils import(
    fc_get_shipstation_rates,
    fc_add_shipping_to_order,
    # fc_get_easyship_rates
)

class OrderItemListCreate(APIView):
    permission_classes = (IsAuthenticated, ) 
    
    def get(self, request):
        user = request.user
        order_detail = OrderDetail.objects.get(user=user, order_status="pending")
        order_items = order_detail.order_items.all().order_by("-created_at")
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        try:
            product = Product.objects.get(pk=product_id)
        except:
            product = None
        if product is None:
            return Response(
                {
                    "error": "Product you selected doesn't exist"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        order_detail = OrderDetail.objects.get(user=user, order_status="pending")
        
        order_item = OrderItem.objects.create(order_detail=order_detail, product=product)
        
        if order_detail.shipping_address is not None:
            country = order_detail.shipping_address.country
            to_zip = order_detail.shipping_address.zip
            add_shipping_to_order = fc_add_shipping_to_order(order_item, country, to_zip)
            if add_shipping_to_order["success"] is False:
                return Response(
                    {
                        "error": add_shipping_to_order["message"],
                        "order_item_id": order_item.id,
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            if order_detail.shipping_method is None:
                order_detail.shipping_method = order_item.shipping_method
            order_detail.amount_shipping = order_detail.amount_shipping + order_item.shipping_rate
            order_detail.amount_paid = order_detail.amount_paid + order_item.shipping_rate
            order_detail.save()       
        
        seralizer = OrderItemSerializer(order_item)
        return Response(seralizer.data,status=status.HTTP_200_OK)

class OrderItemRetrieveUpdateDestroy(APIView):
    permission_classes = (IsAuthenticated, ) 
    
    def get_object(self, pk):
        try:
            return OrderItem.objects.get(pk=pk)
        except OrderItem.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        order_item = self.get_object(pk)
        serializer = OrderItemSerializer(order_item)
        return Response(serializer.data)

    def put(self, request, pk):
        order_item = self.get_object(pk)
        serializer = OrderItemSerializer(order_item, data=request.data, partial=True)        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        order_item = self.get_object(pk)
        order_detail = order_item.order_detail
        order_detail.amount_shipping = order_detail.amount_shipping - order_item.shipping_rate
        order_detail.amount_paid = order_detail.amount_paid - order_item.shipping_rate
        order_detail.save()       
        order_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
        
        
        
class OrderDetailListCreate(APIView):
    permission_classes = (IsAuthenticated, ) 
    
    def get(self, request):
        
        user = request.user
        filter_params = dict()
        desc = request.query_params.get("desc")
        order_status=request.query_params.get("order_status")
        order_by = request.query_params.get("order_by")        
        if desc is not None and order_by is not None:
                desc = convertToBoolean(request.query_params.get("desc"))
                if desc is not None and desc is True:
                    order_by = f"-{order_by}"
        if order_by is None:
                order_by = "-created_at"
        if order_status is not None:
                filter_params["order_status"] = order_status 
        filter_params["user"] = user
        
        order_details = OrderDetail.objects.filter(**filter_params)
        
        # if len(order_details) == 0:
        #     OrderDetail.objects.create(user=user, order_status=order_status)
        #     order_details = OrderDetail.objects.filter(**filter_params).order_by(order_by)
        serializer = OrderDetailSerializer(order_details, many=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        order_detail = OrderDetail.objects.create(user=user)
    
        serializer = OrderDetailSerializer(order_detail)
        return Response(serializer.data)
   
class OrderDetailRetrieveUpdateDestroy(APIView):
    permission_classes = (IsAuthenticated, ) 
    
    def get_object(self, pk):
        try:
            return OrderDetail.objects.get(pk=pk)
        except OrderDetail.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        order_detail = self.get_object(pk)
        serializer = OrderDetailSerializer(order_detail)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        order_detail = self.get_object(pk)
        serializer = OrderDetailSerializer(order_detail, data=request.data, partial=True)
        if serializer.is_valid():
            billing_address_id = request.data.get("billing_address_id")
            shipping_address_id = request.data.get("shipping_address_id")
            payment_id = request.data.get("payment_id")
            if billing_address_id is not None:
                try:
                    billing_address = Address.objects.get(pk=billing_address_id)
                except:
                    return Response(
                        {
                            "error": "Billing address you selected doesn't exist"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
                order_detail.billing_address = billing_address
            shipping_address = None
            if shipping_address_id is not None:
                try:
                    shipping_address = Address.objects.get(pk=shipping_address_id)
                except:
                    return Response(
                        {
                            "error": "Shipping address you selected doesn't exist"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
                amount_shipping = 0
                country = shipping_address.country
                to_zip = shipping_address.zip
                for order_item in order_detail.order_items.all():
                    add_shipping_to_order = fc_add_shipping_to_order(order_item, country, to_zip)
                    if add_shipping_to_order["success"] is False:
                        return Response(
                            {
                                "error": add_shipping_to_order["message"],
                                "order_item_id": order_item.id,
                            }, status=status.HTTP_400_BAD_REQUEST
                        )
                amount_shipping = 0
                amount_paid = 0
                for order_item in order_detail.order_items.all():
                    variant = order_item.product.variants.filter(index=1)[0]
                    inventory = variant.inventory
                    amount_paid += inventory.price * order_item.quantity
                    amount_shipping += order_item.shipping_rate * order_item.quantity
                    
                order_detail.amount_paid = amount_paid + amount_shipping
                order_detail.amount_shipping = amount_shipping
                order_detail.shipping_service_name = order_detail.order_items.all()[0].shipping_service_name
                order_detail.shipping_service_code = order_detail.order_items.all()[0].shipping_service_code
                order_detail.shipping_address = shipping_address             
                
                
                
            if payment_id is not None:
                if len(order_detail.order_items.all()) == 0:
                    return Response(
                        {
                            "error": "no order items included"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
                if order_detail.shipping_address is None:
                    return Response(
                        {
                            "error": "no shipping address included"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
                try:
                    payment = Payment.objects.get(pk=payment_id)
                except:
                    return Response(
                        {
                            "error": "Shipping address you selected doesn't exist"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
                order_detail.payment = payment
                total = 0
                # for order_item in order_detail.order_items.all():
                #     inventory = order_item.product.variants.filter(index=1)[0].inventory
                #     total += inventory.price * order_item.quantity
                create_and_confirm_payment_intent = fc_create_and_confirm_payment_intent(
                    payment.stripe_payment_method_id,
                    order_detail.amount_paid,
                    "usd",
                    user.email,
                    user.stripe_customer_id
                )
                order_detail.amount_paid = total
                if create_and_confirm_payment_intent["success"] is True:
                    order_detail.stripe_payment_intent_id = create_and_confirm_payment_intent["payment_intent"].id
                else:
                    return Response(
                        {
                            "message": create_and_confirm_payment_intent["message"]
                        }, status=status.HTTP_400_BAD_REQUEST
                    )           
            # order_detail.order_status = "confirmed"
            order_detail.save()
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        order_detail = self.get_object(pk)
        order_detail.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class EasyShipRate(APIView):

    def post(self, request):
        result = fc_get_easyship_rates()
        
        return Response(result, status=status.HTTP_200_OK)