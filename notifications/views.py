from django.shortcuts import render

# Create your views here.

from notifications.models import (
    Notification
)

from notifications.serializers import (
    NotificationSerializer
)

from users.models import (
    User
)
from users.serializers import (
    UserMainInfoSerializer
)

from orders.models import (
    OrderDetail
)

from orders.serializers import(
    OrderDetailSerializer
)

from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from products.utils import convertToBoolean


class NotificationListCreate(APIView):
    permission_classes = (IsAuthenticated, ) 
    
    def get(self, request):
        user = request.user
        notifications = Notification.objects.filter(user=user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        inactive_user_id = request.data.get("inactive_user_id")
        order_detail_id = request.data.get("order_detail_id")
        notification_type = request.data.get("notification_type")
        if notification_type is None:
            return Response(
                {
                    "message": "Notification Type Invalid"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        if notification_type == 1 or notification_type == 2:
            if inactive_user_id is None:
                return Response(
                    {
                        "message": "inactive user id needed"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            else:
                try:
                    inactive_user = User.objects.get(pk=inactive_user_id)
                except:
                    inactive_user = None
                if inactive_user is None:
                    return Response(
                        {
                            "message": "inactive user with this id doesn't exist"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    notification = Notification.objects.create(user=user, inactive_user=inactive_user,notification_type=notification_type)
        elif notification_type == 3:
            if order_detail_id is None:
                return Response(
                    {
                        "message": "orderdetail id needed"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            else:
                try:
                    order_detail = OrderDetail.objects.get(pk=order_detail_id)
                except:
                    order_detail = None
                if order_detail is None:
                    return Response(
                        {
                            "message": "order detail with this id doesn't exist"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    notification = Notification.objects.create(user=user, order_detail=order_detail,notification_type=notification_type)
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class NotificationRetrieveUpdateDestory(APIView):
    permission_classes = (IsAuthenticated, ) 

    def get_object(self, pk):
        try:
            return Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        notification = self.get_object(pk)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    
    def put(self, request, pk):
        notification = self.get_object(pk)
        read = request.data.get("read")
        if read is None:
            return Response(
                {
                    "message": "read needed"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            read = convertToBoolean(read)
            notification.read = read
            notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
    
    def delete(self, request, pk):
        notification = self.get_object(pk)
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
