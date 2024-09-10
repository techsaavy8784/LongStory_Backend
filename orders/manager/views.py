# Create your views here.
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
    fc_create_and_confirm_payment_intent,
    fc_create_refund
)   
        
class OrderDetailList(APIView):
    permission_classes = (IsAdminUser, ) 
    
    def get(self, request):
        filter_params = dict()
        desc = request.query_params.get("desc")
        order_status=request.query_params.get("order_status")
        order_by = request.query_params.get("order_by")
        user_id = request.query_params.get("user_id")
        
        if desc is not None and order_by is not None:
            desc = convertToBoolean(request.query_params.get("desc"))
            if desc is not None and desc is True:
                order_by = f"-{order_by}"
        if order_by is None:
            order_by = "-created_at"
        if order_status is not None:
            filter_params["order_status"] = order_status 
        user = None
        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except:
                user = None
        if user is not None:
            filter_params["user"] = user
            
        order_details = OrderDetail.objects.filter(**filter_params).order_by(order_by)
            
        serializer = OrderDetailSerializer(order_details, many=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)
   
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
            if shipping_address_id is not None:
                try:
                    shipping_address = Address.objects.get(pk=shipping_address_id)
                except:
                    return Response(
                        {
                            "error": "Shipping address you selected doesn't exist"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
                order_detail.shipping_address = shipping_address
            order_detail.save()
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        order_detail = self.get_object(pk)
        order_detail.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class CancelOrderDetail(APIView):
    permission_classes = (IsAdminUser, ) 
    
    def get_object(self, pk):
        try:
            return OrderDetail.objects.get(pk=pk)
        except OrderDetail.DoesNotExist:
            raise Http404

    def put(self, request, pk):
        order_detail = self.get_object(pk)
        if order_detail.stripe_invoice_id is None:
            return Response(
                {
                    "message":"Haven't confirmed yet"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        create_refund = fc_create_refund(order_detail.stripe_payment_intent_id)
        if create_refund["success"] is False:
            return Response(
                {
                    "message": create_refund["message"]
                }, status=status.HTTP_400_BAD_REQUEST
            )
        order_detail.stripe_refund_id = create_refund["refund"].id
        order_detail.order_status = "cancelled"
        order_detail.save()
        return Response(
            {
                "refund": create_refund["refund"],
                "order_detail": OrderDetailSerializer(order_detail).data
            }, status=status.HTTP_200_OK
        )
        
        