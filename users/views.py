from users.models import (
    User,
    Address,
    Follow,
    Payment,
    Sponsor,
    Inquiry
)
from users.serializers import (
    UserSigninSerializer,
    UserSerializer,
    AddressSerializer,
    UserInfoSerializer,
    UserMainInfoSerializer,
    FollowSerializer,
    FollowDetailSerializer,
    AddressSerializer,
    PaymentSerializer,
    SponsorSerializer,
    InquirySerializer    
)
from products.models import (
    Like,
    Product
)
from products.serializers import(
    LikeSerializer
)
from users.permissions import IsOwnerOrReadOnly
from django.contrib.auth import authenticate, login, hashers
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import Http404
import requests

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
import random
from products.utils import convertToBoolean
from users.utils import (
    get_client_ip, 
    get_user_device,
    get_country,
    get_country_code,
    fc_validate_address
)
from django.utils import timezone
from django.db.models import Q
from users.paginations import (UserPagination, FollowPagination)
from django.conf import settings
import boto3
import os
from products.utils import (
    generateUniqueFileName,
    convertToBoolean
)
import operator
from payments.views import (
    fc_create_and_attach_payment_method,
    fc_create_payment_model,
    fc_delete_payment_method,
    fc_create_customer,
    fc_create_subscription_with_invoice,
    fc_attach_payment_method_to_customer,
    fc_create_and_confirm_payment_intent,
    fc_modify_default_payment_method,
    fc_cancel_subscription_at_period_end
)
class UserSignupView(APIView):
    """
        signup.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = UserSerializer

    def post(self, request):
        errors = dict()
        serializer = self.serializer_class(data=request.data, partial=True)
        method = request.data.get("method")
        if method is not None and method == "magic":
            request.data["password"] = str(random.randint(10000000, 99999999))
        if serializer.is_valid():            
            user= User.objects.create_user(**serializer.validated_data)
            user.signup_ip = get_client_ip(request)
            user.signup_at = timezone.now()
            user.signup_device = get_user_device(request)
            user.auth_status = 0
            user.save()           
            
            # Mail verification section
            subject = 'Activate Your Account'
            context = {
                'username': user.username,
                'email': user.email,
                'username': user.username,
                # 'domain': settings.DOMAIN,
                'domain': get_current_site(request).domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': token_generator.make_token(user),
            }
            message = render_to_string('users/activate_account.html', context)

            send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False, html_message=message)
        
            
            return Response({
                "context": context,
                "user": serializer.data,
                "message": f"Created new account and mail verification has been sent to {user.email}."
                }, status=status.HTTP_201_CREATED
            )
        else:
            errors = dict()
            errors["success"] = "100"
            if serializer.errors.get("email") is not None:
                errors["email"] = "User with this email already exists"
            if serializer.errors.get("username") is not None:
                errors["username"] = "Username is invalid"
            if serializer.errors.get("password") is not None:
                errors["password"] = "Password is invalid"
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        
class UserUpdateView(APIView):
    permission_classes = (IsAuthenticated, )    

    # Custom get method
    def put(self, request):
        errors = dict()
        try:
            user = request.user
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None:
            serializer = UserInfoSerializer(user, data=request.data, partial=True)
            if(serializer.is_valid()):
                file = request.data.get("file")
                if file is not None:
                    client=boto3.client("s3", aws_access_key_id= settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
                    )
                    file_path = f"image/users/{generateUniqueFileName(file.name)}"
                    try:
                        # Upload the image to S3
                        client.upload_fileobj(file,settings.AWS_STORAGE_BUCKET_NAME,file_path, {'ContentType': "image/png"})
                        
                        # Return the S3 URL
                        s3_url = f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_path}'                            
                    
                    except Exception as e:
                        errors['avatar'] = "upload avatar failed"
                        return Response(errors, status=status.HTTP_400_BAD_REQUEST) 
                    user.avatar_url = s3_url   
                    user.save()               
                
                serializer.save()
                return Response({
                        'user': UserInfoSerializer(user).data,
                        'message': 'User was updated successfully'
                    },status=status.HTTP_200_OK
                )  
            else:
                
                errors["success"] = "100"
                if serializer.errors.get("email") is not None:
                    errors["email"] = "User with this email already exists"
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {
                    'data': None,
                    'message': 'Failed to create username'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

class UserRecendActivationMail(APIView):
    """
        Recend Activation Mail.
    """
    permission_classes = (IsAuthenticated,)
    # authentication_classes = ()

    def post(self, request):
        user = request.user
        #Mail verification section
        subject = 'Activate Your Account'
        context = {
            'username': user.username,
            'email': user.email,
            'domain': get_current_site(request).domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': token_generator.make_token(user),
        }
        message = render_to_string('users/activate_account.html', context)

        send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False, html_message=message)

        return Response({
            "message": f"mail verification has been resent to {user.email}."
            }, status=status.HTTP_200_OK
        )
        
class UserRecendMagicLink(APIView):
    """
        Recend Activation Mail.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
        except:
            user = None
            return Response({
            "message": "User with this email doesnot exist ."
            }, status=status.HTTP_200_OK
        )
        if hasattr(user, 'is_active'):
                    
            # Mail verification section
            subject = 'Signin to Long Story Short'
            context = {
                'email': user.email,
                'domain': settings.DOMAIN,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': token_generator.make_token(user),
            }
            message = render_to_string('users/signin_to_lss.html', context)

            send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [
                      user.email], fail_silently=False, html_message=message)

            return Response({
                "user": UserInfoSerializer(user).data,
                "message": f"Created new account and mail verification has been sent to {user.email}."
                }, status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {
                    "error": "Email not active",
                },
                status=401,
            )


class UserAccountActivateView(APIView):
    permission_classes = (AllowAny, )    

    # Custom get method
    def get(self, request, uidb64, token):

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and token_generator.check_token(user, token):
            user.mail_verified = True
            user.auth_status = 1
            user.last_signin_at = get_client_ip(request)
            user.last_signin_at = timezone.now()
            user.save()
            
            login(request, user)
            refresh = RefreshToken.for_user(user)
            
            data = {
                "tokenObj": {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                "user": UserInfoSerializer(instance=user).data
            }
            return Response(data,status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'data': None,
                    'message': 'Failed to verify your email'
                },
                status=status.HTTP_400_BAD_REQUEST
            )      
            
class UserGetToken(APIView):
    permission_classes = (AllowAny, )    

    # Custom get method
    def get(self, request, uidb64, token):

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and token_generator.check_token(user, token):            
            
            if hasattr(user, 'is_active'):
                # login(request, user)
                refresh = RefreshToken.for_user(user)
                user.last_signin_at = get_client_ip(request)
                user.last_signin_at = timezone.now()
                user.save()
                data = {
                    "tokenObj": {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    "user": UserInfoSerializer(instance=user).data
                }
                
                return Response(
                    data=data,
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        "error": "Email not active",
                    },
                    status=401,
                )            
            
        else:
            return Response(
                {
                    'data': None,
                    'message': 'Failed to get token'
                },
                status=status.HTTP_400_BAD_REQUEST
            )      
    
            
class UserResetPasswordView(APIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated)
    def put(self, request):
        user = request.user
        new_password = request.data['new_password']
        old_password = request.data['old_password']
        matched = hashers.check_password(old_password, user.password)
        if matched:
            user.password = hashers.make_password(new_password)
            user.save()
            return Response(
                {
                    'data': None,
                    'message': 'Password has been updated successfully'
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'data': None,
                    'message': 'Bad Request'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
class UserForgotPasswordView(APIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny, ) 
    # User Forgot password   

    def get(self, request):
        email = request.query_params.get('email')
        try:
            user = User.objects.get(email=email)           
            
        except User.DoesNotExist:
            user = None
        if user is not None:
            random_num = random.randint(1000, 9999)
            user.otp = random_num
            user.save()
            subject = 'Forgot Password'
            context = {
                'email': user.email,
                'username': user.username,
                # 'domain': settings.DOMAIN,
                'domain': get_current_site(request).domain,
                'otp':  random_num
            }
            message = render_to_string('users/forgot_password.html', context)

            try:
                success =  send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False, html_message=message)
            except:
                success = 0
            if success == 1:                
                return Response(
                    {                    
                        'message': "Reset password mail has been sent"
                    },status=status.HTTP_200_OK                
                )
            else:
                return Response(
                {                    
                    'error': "Failed to send mail"
                },status=status.HTTP_400_BAD_REQUEST                
            )
        else:
            return Response(
                {                    
                    'error': "User with this email doesn't exist"
                },status=status.HTTP_400_BAD_REQUEST                
            )
            
class UserCheckOTP(APIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny, ) 
    # User Forgot password   

    def get(self, request):
        email = request.query_params.get('email')
        otp = request.query_params.get('otp')
        try:
            user = User.objects.get(email=email)           
            
        except User.DoesNotExist:
            user = None
        if user is not None:
            if otp is None:                
                return Response(
                    {                    
                        'error': "Need fill otp"
                    },status=status.HTTP_400_BAD_REQUEST 
                )
            else:
                if user.otp == otp:
                    return Response(
                        {                    
                            'message': "verifying OTP success"
                        },status=status.HTTP_200_OK                
                    )
                else:
                    return Response(
                        {                    
                            'error': "OTP doesn't match"
                        },status=status.HTTP_400_BAD_REQUEST                
                    )
        else:
            return Response(
                {                    
                    'error': "User with this email doesn't exist"
                },status=status.HTTP_400_BAD_REQUEST                
            )
            
class UserChangePassword(APIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny, ) 
    # User Forgot password   

    def put(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=email)           
            
        except User.DoesNotExist:
            user = None
        if user is not None:
            if password is None:                
                return Response(
                    {                    
                        'error': "Need fill password"
                    },status=status.HTTP_400_BAD_REQUEST 
                )
            else:
                user.password = hashers.make_password(password)
                user.save()
                return Response(
                    {                    
                        'message': "change password success",
                        'password': user.password,
                    },status=status.HTTP_200_OK                
                )                
        else:
            return Response(
                {                    
                    'error': "User with this email doesn't exist"
                },status=status.HTTP_400_BAD_REQUEST                
            )
        

class UserSigninView(APIView):
    """
        signin.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()
    serializer_class = UserSigninSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer["email"].value
            password = request.data["password"]
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                if hasattr(user, 'is_active'):
                    # login(request, user)
                    refresh = RefreshToken.for_user(user)
                    user.last_signin_ip = get_client_ip(request)
                    user.last_signin_at = timezone.now()
                    user.last_signin_device = get_user_device(request)
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
                        "user": UserInfoSerializer(instance=user).data
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
    
class UserMeView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):        
        user = request.user
        serializer = UserInfoSerializer(user)
        return Response({"user":serializer.data}, status=status.HTTP_200_OK)
    
class UserAuthStatusView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request):        
        user = request.user
        serializer = UserInfoSerializer(user)
        return Response({"auth_status": user.auth_status, "auth_token": user.auth_token}, status=status.HTTP_200_OK)
        
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
        
class AddressListCreate(APIView):
    permission_classes = (IsAuthenticated, ) 
    def get(self, request):
        addresses = Address.objects.filter(user=request.user).order_by("created_at").order_by("id")             
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        user = request.user
        if serializer.is_valid():
            address_to_validate = f"{request.data.get('address')}, {request.data.get('city')}, {request.data.get('country')}"
            print(address_to_validate)
            validate_address = fc_validate_address(address_to_validate)
            if validate_address["success"] is False:
                return Response(
                    {
                        "message":validate_address["message"]
                    }, status=status.HTTP_400_BAD_REQUEST
                )                
            postal_code = validate_address["postal_code"]
            if str(postal_code) != request.data.get("zip"):
                return Response(
                    {
                        "message": "postal code unmatched to the given address"
                    }, status=status.HTTP_400_BAD_REQUEST
                )   
            address = Address.objects.create(**serializer.validated_data, user=user)
            return Response(AddressSerializer(address).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class AddressRetrieveUpdateDestroy(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = AddressSerializer
    
    def get_object(self, pk):
        try:
            return Address.objects.get(pk=pk)
        except Address.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        address = self.get_object(pk)
        serializer = AddressSerializer(address)
        return Response(serializer.data)

    def put(self, request, pk):
        user = request.user
        address = self.get_object(pk)
        self.check_object_permissions(request, address)
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            is_default = convertToBoolean(request.data.get("is_default"))
            
            address_to_validate = f"{serializer.validated_data.get('address')}, {serializer.validated_data.get('city')}, {serializer.validated_data.get('country')}"
            validate_address = fc_validate_address(address_to_validate)
            if validate_address["success"] is False:
                return Response(
                    {
                        "message":validate_address["message"]
                    }, status=status.HTTP_400_BAD_REQUEST
                )                
            postal_code = validate_address["postal_code"]
            if str(postal_code) != serializer.validated_data.get("zip"):
                return Response(
                    {
                        "message": "postal code unmatched to the given address"
                    }, status=status.HTTP_400_BAD_REQUEST
                )   
            
            
            if is_default is not None and is_default is True:
                try:
                    default_address = user.addresses.get(is_default=True)
                except:
                    default_address = None
                if default_address is not None:
                    default_address.is_default = False
                    default_address.save()
                address.is_default = True
                address.save()     
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        address = self.get_object(pk)
        self.check_object_permissions(request, address)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class PaymentListCreate(APIView):
    permission_classes = (IsAuthenticated, ) 
    def get(self, request):
        payments = Payment.objects.filter(user=request.user) 
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        user = request.user
        type = request.data.get("type")
        token_id = request.data.get("token_id")
        ###
        create_payment_method = fc_create_and_attach_payment_method(type, token_id, user.stripe_customer_id)
        if create_payment_method["success"] is False:
            return Response(
                {
                    "error": create_payment_method["message"]
                }, status=status.HTTP_400_BAD_REQUEST
            )
        create_payment_model = fc_create_payment_model(create_payment_method["payment_method"], user)
        if create_payment_model["success"] is False:
            return Response(
                {
                    "error": create_payment_model["message"]
                }, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = PaymentSerializer(create_payment_model["payment"])
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    
class PaymentRetrieveUpdateDestroy(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    # permission_classes = (IsAdminUser, )
    serializer_class = PaymentSerializer
    
    
    def get_object(self, pk):
        try:
            return Payment.objects.get(pk=pk)
        except Payment.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        payment = self.get_object(pk)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)

    def put(self, request, pk):
        payment = self.get_object(pk)
        self.check_object_permissions(request, payment)
        user = request.user
        serializer = PaymentSerializer(payment, data=request.data, partial=True)
        if serializer.is_valid():
            is_default = convertToBoolean(request.data.get("is_default"))
            if is_default is not None and is_default is True:
                try:
                    default_payment = user.payments.get(is_default=True)
                except:
                    default_payment = None
                if default_payment is not None:
                    default_payment.is_default = False
                    default_payment.save()
                payment.is_default = True
                payment.save()     
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        payment = self.get_object(pk)
        self.check_object_permissions(request, payment)
        ###
        delete_payment_method = fc_delete_payment_method(payment.stripe_payment_method_id)
        if delete_payment_method["success"] is False:
            return Response(
                {
                    "error": delete_payment_method["message"]
                }, status=status.HTTP_400_BAD_REQUEST
            )
        payment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class LikeList(APIView):
    permission_classes = (IsAuthenticated, ) 
    def get(self, request):
        user = request.user
        likes = Like.objects.filter(user=user).order_by("-created_at")        
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)
    
class LikeRetrieveCreateDestroy(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        user = request.user
        try:
            product = Product.objects.get(pk=pk)
        except:
            product = None
        if product is None:
            return Response(
                {
                    "error": "product doen't exist"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            like = Like.objects.get(user=user, product=product)
        except:
            like = None
        if like is None:
            return Response(
                {
                    "error": "you haven't liked this product yet"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = LikeSerializer(like)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request, pk):
        user = request.user
        try:
            product = Product.objects.get(pk=pk)
        except:
            product = None
        if product is None:
            return Response(
                {
                    "error": "product doen't exist"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            like = Like.objects.get(user=user, product=product)
        except:
            like = None
        if like is not None:
            return Response(
                {
                    "error": "you already liked this product"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        like = Like.objects.create(user=user, product=product)
        serializer = LikeSerializer(like)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        user = request.user
        try:
            product = Product.objects.get(pk=pk)
        except:
            product = None
        if product is None:
            return Response(
                {
                    "error": "product doen't exist"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            like = Like.objects.get(user=user, product=product)
        except:
            like = None
        if like is None:
            return Response(
                {
                    "error": "you haven't liked this product yet"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        like.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserFollowRetrieveView(APIView):
    # permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        user_id=request.query_params.get("user_id")
        if(user_id == None):
            user = request.user
        else:
            user = User.objects.get(pk=user_id)
        followers = user.followers.all()
        followees = user.followees.all()
        result = dict()
        result["followers_total_count"] = len(followers)
        result["followees_total_count"] = len(followees)
        
        return Response(
            result, status=status.HTTP_200_OK
        )
            
    
    
class UserFollowerListView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        user = request.user
        filter_params = dict()
        if request.query_params.get("is_active") is not None:
            is_active = convertToBoolean(request.query_params.get("is_active"))
            if is_active is not None:
                filter_params["is_active"] = is_active
        if request.query_params.get("is_accepted") is not None:
            is_accepted = convertToBoolean(request.query_params.get("is_accepted"))
            if is_accepted is not None:
                filter_params["is_accepted"] = is_accepted
        
        followers = user.followers.filter(**filter_params).order_by("-created_at")
        if request.query_params.get("search") is not None:
            search = request.query_params.get("search")
            followers = followers.filter(Q(follower__username__icontains=search) | Q(follower__email__icontains=search))
        paginator = FollowPagination()
        queryset =paginator.paginate_queryset(followers, request)
        serializer = FollowDetailSerializer(queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

class UserFollowerRetrieveUpdateView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def put(self, request, pk):
        user = request.user
        try:
            follower = user.followers.get(follower_id = pk)
        except:
            follower = None
        if follower is None:
            return Response(
                {
                    "error": "User you are gonna allow following you doesn't exist"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        is_accepted = convertToBoolean(request.data.get("is_accepted"))
        if is_accepted is None:
            return Response(
                {
                    "error": "need is_accepted field to be valid boolean"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        follower.is_accepted = is_accepted
        follower.save()
        seralizer = FollowDetailSerializer(follower)
        return Response(seralizer.data, status=status.HTTP_200_OK)
            

class UserFolloweeListView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
        user = request.user
        filter_params = dict()
        if request.query_params.get("is_active") is not None:
            is_active = convertToBoolean(request.query_params.get("is_active"))
            if is_active is not None:
                filter_params["is_active"] = is_active
        if request.query_params.get("is_accepted") is not None:
            is_accepted = convertToBoolean(request.query_params.get("is_accepted"))
            if is_accepted is not None:
                filter_params["is_accepted"] = is_accepted
                
        # is_accepted filed should be true
        followees = user.followees.filter(**filter_params).order_by("-created_at")
        total = len(followees)
        if request.query_params.get("search") is not None:
            search = request.query_params.get("search")
            followees = followees.filter(Q(followee__username__icontains=search) | Q(followee__email__icontains=search)) 
        paginator = FollowPagination()
        queryset =paginator.paginate_queryset(followees, request)
        serializer = FollowDetailSerializer(queryset, many=True)
        response = paginator.get_paginated_response(serializer.data)
        
        return response
    
class UserFolloweeCreateRetrieveUpdateView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, pk):
        user = request.user
        try:
            followeeUser = User.objects.get(pk=pk)
        except:
            followeeUser = None 
        if followeeUser is None:
            return Response(
                {
                    "error": "User you are gonna follow doesn't exist"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            followee = user.followees.get(followee=followeeUser)
        except:
            followee = None
        if followee is not None:
            return Response(
                {
                    "error": "You already follow this user"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        followee = Follow.objects.create(follower=user, followee=followeeUser)
        seralizer = FollowDetailSerializer(followee)
        return Response(seralizer.data, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        user = request.user
        try:
            followee = user.followees.get(followee_id = pk)
        except:
            followee = None
        if followee is None:
            return Response(
                {
                    "error": "User you are gonna unfollow or follow doesn't exist"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        is_active = convertToBoolean(request.data.get("is_active"))
        if is_active is None:
            return Response(
                {
                    "error": "need is_active field to be valid boolean"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        followee.is_active = is_active
        if not is_active:
            followee.is_accepted = False
        followee.save()
        seralizer = FollowDetailSerializer(followee)
        return Response(seralizer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        user = request.user
        try:
            followee = User.objects.get(pk=pk)
        except:
            followee = None
        if followee is None:
            return Response(
                {
                    "error": "User you are gonna unfollow or follow doesn't exist"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            follow = Follow.objects.get(followee=followee, follower=user)
        except:
            return Response(
                {
                    "error": "You haven't follow this user yet"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class SponsorListCreate(APIView):
    permission_classes = (IsAuthenticated, )  

    def get(self, request):
        sponsor_user = request.user
        sponsored_users = sponsor_user.sponsored_users.all()
        return Response(
            SponsorSerializer(sponsored_users, many=True).data, status=status.HTTP_200_OK
        )
    
    def post(self, request):
        sponsor_user = request.user
        sponsored_user = None
        sponsor = None
        subscription_payment = None
        order_payment = None
        username = request.data.get("username")
        email = request.data.get("email")
        subscription_payment_id = request.data.get("subscription_payment_id")
        order_payment_id = request.data.get("order_payment_id") 
        if email is None:
            return Response(
                {
                    "message": "You didn't include user info you are gonna sponsor"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            sponsored_user = User.objects.get(email=email)
        except:
            sponsored_user = None

        if subscription_payment_id is not None:
            try:
                subscription_payment = sponsor_user.payments.get(pk=subscription_payment_id)
            except:
                return Response(
                {
                    "message": "Payment for subscribing sponsor is invalid"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            subscription_payment = None
            
        if order_payment_id is not None:
            try:
                order_payment = sponsor_user.payments.get(pk=order_payment_id)
            except:
                return Response(
                    {
                        "message": "Payment for subscribing sponsor is invalid"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            order_payment = None
        
        if sponsored_user is None:
            password = str(random.randint(10000000, 99999999))
            new_user = {
                "email": email,
                "password": password
            }
            if username is not None:
                new_user["username"] = username
            
            try:
                sponsored_user = User.objects.create(**new_user)
                create_customer = fc_create_customer(sponsored_user)
                if create_customer["success"] is False:
                    return Response(
                        {
                            "message": f"failed to create stripe customer for {sponsored_user.username}: {create_customer['message']}"
                        },status=status.HTTP_400_BAD_REQUEST
                    )
                sponsored_user.stripe_customer_id = create_customer["customer_id"]
                sponsored_user.auth_status = 8
                sponsored_user.save()
            except:
                sponsored_user = None

        if sponsored_user is None:
            return Response(
                {
                    "message": "Failed to create sponsored user"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            try:
                sponsor = Sponsor.objects.get(pk=sponsored_user.id)
            except:
                sponsor = None
            if sponsor is not None:
                return Response(
                    {
                        "message": f"User you are gonna sponsor has already been sponsored by {sponsor.sponsor_user.username}"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            else:
                sponsor = Sponsor.objects.create(sponsored_user=sponsored_user, sponsor_user=sponsor_user)

            if subscription_payment is not None:
                sponsor.subscription_payment = subscription_payment
                if sponsored_user.auth_status != 9:
                    create_subscription_with_invoice = fc_create_subscription_with_invoice(sponsor_user.stripe_customer_id, subscription_payment.stripe_payment_method_id)
                    if create_subscription_with_invoice["success"] is False:
                        return Response(
                            {
                                "message": f"create subscription for {sponsored_user.username} by {sponsor.username} failed: {create_subscription_with_invoice['message']}"
                            }, status=status.HTTP_400_BAD_REQUEST
                        )
                    sponsored_user.stripe_subscription_id = create_subscription_with_invoice["subscription_id"]
                    
                    sponsored_user.auth_status = 9
                    sponsored_user.save()   
                else:
                    pass             
            if order_payment is not None:
                sponsor.order_payment = order_payment
            sponsor.save()
            
            return Response(SponsorSerializer(sponsor).data, status=status.HTTP_201_CREATED)
        
class SponsorRetrieveUpdate(APIView):
    permission_classes=(IsAuthenticated,)

    def get_object(self, pk):
        try:
            return Sponsor.objects.get(pk=pk)
        except Sponsor.DoesNotExist:
            raise Http404

    def get(self, request, pk):

        sponsor = self.get_object(pk)
        return Response(SponsorSerializer(sponsor).data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):

        sponsor = self.get_object(pk)
        sponsored_user = sponsor.sponsored_user

        subscription_payment_id = request.data.get("subscription_payment_id")
        order_payment_id = request.data.get("order_payment_id")

        if subscription_payment_id is not None:
            if subscription_payment_id == -1:
                sponsor.subscription_payment = None
                cancel_subscription_at_period_end = fc_cancel_subscription_at_period_end(sponsored_user.stripe_subscription_id)
                if cancel_subscription_at_period_end["success"] is False:
                    return Response(
                        {
                            "message":f"Failed to cancel stripe subscription: {cancel_subscription_at_period_end['message']}"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
                
            else:
                try:
                    subscription_payment = Payment.objects.get(pk=subscription_payment_id)
                except:
                    subscription_payment = None
                if subscription_payment is None:
                    return Response({
                        "message":"Payment for subscribing sponsored user invalid"
                    },status=status.HTTP_400_BAD_REQUEST)
                else:
                    sponsor.subscription_payment = subscription_payment
                    sponsor.sponsored_user.auth_status = 9
                    sponsor.sponsored_user.save()

        if order_payment_id is not None:
            if order_payment_id == -1:
                sponsor.order_payment = None
            else:
                try:
                    order_payment = Payment.objects.get(pk=order_payment_id)
                except:
                    order_payment = None
                if order_payment is None:
                    return Response({
                        "message":"Payment for sponsored user to order product invalid"
                    },status=status.HTTP_400_BAD_REQUEST)
                else:
                    sponsor.order_payment = order_payment
        sponsor.save()        
        return Response(SponsorSerializer(sponsor).data, status=status.HTTP_202_ACCEPTED)
    
class InquiryView(APIView):
    permission_classes=(IsAuthenticated,)
    
    def get(self, request):
        user = request.user
        inqueries = Inquiry.objects.all()
        serializer = InquirySerializer(inqueries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        persona_inquiry_id = request.data.get("persona_inquiry_id")
        if persona_inquiry_id is None:
            return Response(
                {
                    "message": "Persona Inquiry id is required"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        inquiry = Inquiry.objects.create(user=user, persona_inquiry_id = persona_inquiry_id)
        serializer = InquirySerializer(inquiry)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        user = request.user
        inquiry = Inquiry.objects.get(user=user)
        status = request.data.get("status")
        inquiry.status = status
        if status == "approved":
            user.auth_status = 3
            user.save()
        inquiry.save()
        serializer = InquirySerializer(inquiry)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request):
        user = request.user
        inquiry = Inquiry.objects.get(user=user)
        inquiry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class PersonaInquiryRetrieve(APIView):
    permission_classes = (IsAuthenticated)
    
    def get(self, request):
        user = request.user
        inquiry = Inquiry.objects.get(user=user)
        url = f"https://withpersona.com/api/v1/inquiries/{inquiry.persona_inquiry_id}/resume"

        headers = {
            "accept": "application/json",
            "Persona-Version": "2023-01-05",
            "authorization": f"Bearer {settings.PERSONA_API_KEY}"
        }

        response = requests.post(url, headers=headers)
    


        

            
        



            


    
        
    
        
        
