from users.models import (
    User,
    Address
)
from users.serializers import (
    UserSigninSerializer,
    UserSerializer,
    AddressSerializer,
    UserInfoSerializer,
    UserMainInfoSerializer
    
)
from django.contrib.auth import authenticate, login, hashers
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import Http404

from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes
from users.token import token_generator
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.encoding import force_str, force_bytes

from django.contrib.sites.shortcuts import get_current_site
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.db.models import Q
from users.utils import get_client_ip
from products.utils import convertToBoolean
from django.utils import timezone
from users.paginations import UserPagination
from users.token import generate_auth_token

class UserSignupView(APIView):
    """
        signup.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = UserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user= User.objects.create_user(**serializer.validated_data)
            user.is_staff = True
            user.is_superuser = True
            user.signup_ip = get_client_ip(request)
            user.signup_at = timezone.now()
            user.save()

            return Response({
                "user": serializer.data,
                "message": f"Created new admin account."
                }, status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class UserSendInvitation(APIView):
    # permission_classes = (IsAuthenticated,)
    def put(self, request):        
        user_id = request.data.get("user_id")
        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except:
                return Response({
                    "message": f"User with id {user_id} doesn't exist."
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            if user.auth_status == 5:
                user.auth_token = (timezone.now() - timezone.datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds() + 72 * 3600
                user.auth_status = 7
                user.save()
                return Response({
                    "message": f"sent invitation to id {user.id}"
                    }, status=status.HTTP_200_OK
                )
            else:
                return Response({
                    "message": f"User with id {user_id} hasn't submitted yet. Or already approved"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({
            "message": f"user_id needed"
            }, status=status.HTTP_400_BAD_REQUEST
        )
            
        
    
class UserSigninView(APIView):
    """
        signin.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = UserSigninSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer["email"].value
            password = request.data["password"]

            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                if hasattr(user, 'is_active'):
                    login(request, user)
                    refresh = RefreshToken.for_user(user)
                    user.last_signin_ip = get_client_ip(request)
                    user.last_signin_at = timezone.now()
                    if user.first_signin_at is None:
                        user.first_signin_at = timezone.now()
                    if user.first_signin_ip is None:
                        user.first_signin_ip = get_client_ip(request)
                    user.save()                                
                    
                    
                    data = {
                        "tokenObj": {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        },
                        "user": self.serializer_class(instance=user).data
                    }
                    return Response(
                        data=data,
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {
                            "error": "Email not verified",
                        },
                        status=401,
                    )

            return Response({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserList(APIView):
    permission_classes = (AllowAny,)
    def get(self, request):
        filter_params = dict()
        user_type = request.query_params.get("user_type")
        order_by = request.query_params.get("order_by")
        
        if request.query_params.get("desc") is not None and order_by is not None:
            desc = convertToBoolean(request.query_params.get("desc"))
            if desc is not None and desc is True:
                order_by = f"-{order_by}"  
        if order_by is None:
            order_by = "-created_at"
        if request.query_params.get("is_active") is not None:
            is_active = convertToBoolean(request.query_params.get("is_active"))
            if is_active is not None:
                filter_params["is_active"] = is_active
                
        if user_type is not None and user_type == "general":
            filter_params["is_staff"] = False
        elif user_type is not None and user_type == "staff":
            filter_params["is_staff"] = True   
        elif user_type is not None and user_type == "superuser":
            filter_params["is_superuser"] = True
        if len(filter_params) > 0:    
            users = User.objects.filter(**filter_params).order_by(order_by)
        else:
            users = User.objects.all().order_by(order_by)    
                   
        if request.query_params.get("search") is not None:
            search = request.query_params.get("search")
            users = users.filter(Q(username__icontains=search) | Q(email__icontains=search))       
            
        paginator = UserPagination()
        queryset =paginator.paginate_queryset(users, request)
        serializer = UserInfoSerializer(queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class UserRetrieveUpdateDestroy(APIView):
    
    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404    
    
    def get(self, request, pk):
        user = self.get_object(pk)
        serializer = UserInfoSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        user = self.get_object(pk)
        serializer = UserMainInfoSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            addresses = request.data.get("addresses")
            invalid_addresses = []
            address_does_not_exist_in_db = []
            if addresses is not None:
                for address in addresses:
                    id = address.get("id")
                    is_deleted = address.get("is_deleted")
                    addressserializer = AddressSerializer(data=address)
                    if is_deleted is None and not addressserializer.is_valid():
                        invalid_addresses.append(address)
                    if id is not None:
                        try:
                            address_searched = Address.objects.get(pk=address["id"])
                        except:
                            address_does_not_exist_in_db.append(address)
                if len(invalid_addresses) > 0:
                    return Response(
                        {
                            "message": "included addresses that have invalid address info",
                            "invalid_addresses": invalid_addresses
                        }
                    )
                if len(address_does_not_exist_in_db) > 0:
                    return Response(
                        {
                            "message": "included addresses that don't exist in db",
                            "address_does_not_exist_in_db": address_does_not_exist_in_db
                        }
                    )
                for address in addresses:
                    id = address.get("id")
                    is_deleted = address.get("is_deleted")
                    if id is None:
                        address_created = Address.objects.create(
                            user = user,
                            address = address["address"],
                            city = address["city"],
                            country = address["country"],
                            phone = address["phone"],
                            postal_code = address["postal_code"],                       
                        )
                    if id is not None and is_deleted is not None and is_deleted == True:
                        Address.objects.get(pk=id).delete()
                    if id is not None and is_deleted is None:
                        address_should_updated = Address.objects.get(pk=id)
                        addressserializer = AddressSerializer(address_should_updated, data=address, partial=True)
                        if addressserializer.is_valid():
                            addressserializer.save()                
            serializer.save()
            return Response(UserInfoSerializer(user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        user = self.get_object(pk)
        user.delete()
        return Response(
            {
                "message": "selected user is deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT
        )
        
        
