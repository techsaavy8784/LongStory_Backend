from products.models import (
    Category,
    Product,
    Variant,
    Metadata,
    Media,
    Inventory,
    Like,
    Shipping
)
from products.serializers import(
    CategorySerializer,
    ProductSerializer,
    VariantSerializer,
    MetadataSerializer,
    MediaSerializer,
    InventorySerializer,
    LikeSerializer, 
    VariantDetailedInfoSerializer,
    ProductDetailedInfoSerializer,
    ShippingSerializer
)

from rest_framework.response import Response
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.db.models import Q
from django.conf import settings
import boto3
import os
from products.utils import (
    generateUniqueFileName,
    convertToBoolean
)
from .paginations import ProductPagination
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from django.http import JsonResponse
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload
import io

class CategoryListCreate(APIView):
    permission_classes = (AllowAny, )    
    # permission_classes = (IsAdminUser, )    
    def get(self, request):
        filter_params = dict()
        is_active = request.query_params.get("is_active")
        if is_active is not None:
            is_active = convertToBoolean(is_active)
            if is_active is not None:
                filter_params["is_active"] = is_active
        if len(filter_params) > 0:
            categories = Category.objects.filter(**filter_params)
        else:
            categories = Category.objects.all()   
        if request.query_params.get("search") is not None:
            search = request.query_params.get("search")
            categories = categories.filter(Q(name__icontains=search) | Q(description__icontains=search))
                                 
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CategoryRetrieveUpdateDestroy(APIView):
    permission_classes = (AllowAny, )
    # permission_classes = (IsAdminUser, )
    
    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        category = self.get_object(pk)
        serializer = CategorySerializer(category)
        
        return Response(serializer.data)

    def put(self, request, pk):
        category = self.get_object(pk)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk)
        category.is_active = False
        category.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class ProductBulkUpdate(APIView):
    permission_classes = (AllowAny, )
    
    def put(self, request):
        category_id = request.data.get("category_id")
        is_active = request.data.get("is_active")
        is_soldout = request.data.get("is_soldout")
        is_selected_all = request.data.get("is_selected_all")
        product_ids = request.data.get("product_ids")
        products = None
        if product_ids is None or len(product_ids) == 0 or ((product_ids is None or len(product_ids) == 0) and not is_selected_all):
            return Response(
                {
                    "message": "you didn't select any product"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            if is_selected_all:
                products = Product.objects.filter(category=category_id)
            else:    
                products = Product.objects.filter(pk__in=product_ids)   
        
        if is_active is None and is_soldout is None and category_id is None:
            return Response(
                {
                    "message": "you should include is_active or is_soldout or category_id"
                }, status=status.HTTP_400_BAD_REQUEST
            )
        if is_active is not None:
            products.update(is_active=convertToBoolean(is_active))
        if is_soldout is not None:
            for product_id in product_ids:
                variants = Variant.objects.filter(product_id=product_id)
                if variants.exists():
                    for variant in variants:
                        inventory = Inventory.objects.get(pk=variant.id)
                        if is_soldout:
                            inventory.quantity = 0
                        else:
                            inventory.quantity = 1
                        inventory.save()
        if category_id is not None:
            if category_id == -1:
                products.update(category=None)
            else:
                try:
                    category = Category.objects.get(pk=category_id)
                except:
                    category = None
                if category is not None:
                    products.update(category=category)         
                    
                else:
                    return Response(
                        {
                            "message": "category with requested id doesn't exist"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
        return Response(
            {
                "message": f"updated {len(products)} products successfully",
                "length": len(products)
                # "products": ProductSerializer(products,many=True).data
            },status=status.HTTP_200_OK
        )
            

class ProductListCreate(APIView):
    permission_classes = (AllowAny, )
    # pagination_class = ProductPagination
    
    def get(self, request):
        
        filter_params = dict()
        order_by = request.query_params.get("order_by")
        category_id = request.query_params.get("category_id")
        
        
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
        if request.query_params.get("is_published") is not None:
            is_published = convertToBoolean(request.query_params.get("is_published"))
            if is_published is not None:
                filter_params["is_published"] = is_published               
        if len(filter_params) > 0:    
            products = Product.objects.filter(**filter_params).order_by(order_by)
        else:
            products = Product.objects.all().order_by(order_by)
            
        if request.query_params.get("search") is not None:
            search = request.query_params.get("search")
            products = products.filter(Q(name__icontains=search) | Q(description__icontains=search)| Q(variants__metadata__field__icontains=search) | Q(variants__metadata__value__icontains=search)).distinct()
        if category_id is not None:
            if category_id == "-1":
                products = products.filter(category=None)
            elif category_id > "0":
                products = products.filter(category=category_id)
        if request.query_params.get("is_soldout") is not None:
            is_soldout = convertToBoolean(request.query_params.get("is_soldout"))
            if is_soldout is not None:
                if is_soldout:
                    products = products.filter(
                        Q(variants__inventory__quantity=0) |
                        Q(variants__isnull=True) |
                        Q(variants__inventory__isnull=True)
                    )
                else:
                    products = products.filter(
                        Q(variants__isnull=False) &
                        Q(variants__inventory__isnull=False) &
                        Q(variants__inventory__quantity__gt=0)
                    )

        paginator = ProductPagination()            
        queryset =paginator.paginate_queryset(products, request)
        serializer = ProductDetailedInfoSerializer(queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request):
        productSerializer = ProductSerializer(data=request.data)
        if productSerializer.is_valid():
            category_id = request.data.get("category_id")
            if category_id is not None:
                try:
                    category = Category.objects.get(pk=category_id)
                except:
                    return Response(
                    {
                        "message": "selected category doesn't exist"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            product = Product.objects.create(**productSerializer.validated_data)
            if category_id is not None:
                product.category = category
            product.save()            
            serializer = ProductDetailedInfoSerializer(product)          
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(productSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProductRetrieveUpdateDestroy(APIView):
    permission_classes = (AllowAny, )
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise Http404    
    def get(self, request, pk):
        product = self.get_object(pk)
        serializer = ProductDetailedInfoSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def put(self, request, pk):
        product = self.get_object(pk)
        category_id = request.data.get("category_id")
        is_active = request.data.get("is_active")
        is_soldout = request.data.get("is_soldout")
        is_published = request.data.get("is_published")
        published_at = request.data.get("published_at")        
        
        productSerializer = ProductSerializer(product, data=request.data, partial=True)
        if productSerializer.is_valid():
            if category_id is not None and category_id != -1:
                # print(isinstance(category_id,int))
                try:
                    category = Category.objects.get(pk=category_id)
                except:
                    return Response(
                    {
                        "message": "selected category doesn't exist"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
                product.category = category
                product.save()
                productSerializer.save() 
            if is_active is not None:
                product.is_active = is_active
                product.save()
                productSerializer.save()
            if is_published is not None:
                product.is_published = is_published
                product.published_at = published_at
                product.save()
                productSerializer.save()
            if is_soldout is not None:
                variants = Variant.objects.filter(product_id=pk)
                if variants.exists():
                    for variant in variants:
                        inventory = Inventory.objects.get(pk=variant.id)
                        if is_soldout:
                            inventory.quantity = 0
                        else:
                            inventory.quantity = 1
                        inventory.save()
       
            return Response(productSerializer.data, status=status.HTTP_201_CREATED)
        return Response(productSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        product = self.get_object(pk)
        product.is_active = False
        product.save()
        return Response(
            {
                "message": "selected product is deactivated successfully"
            }, status=status.HTTP_204_NO_CONTENT
        )
        
class VariantListCreate(APIView):
    permission_classes = (AllowAny, )
    def get(self, request):
        is_active = request.query_params.get("is_active")
        product_id = request.query_params.get("product_id")
        product = Product.objects.get(id=product_id)
        if is_active is not None and is_active=="true":
            
            variants = Variant.objects.filter(is_active=True, product=product)
        elif is_active is not None and is_active=="false":
            variants = Variant.objects.filter(is_active=False, product=product)
        elif is_active is None:
            variants = Variant.objects.filter(product=product)        
        serializer = VariantDetailedInfoSerializer(variants, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request):
        variantSerializer = VariantSerializer(data=request.data)
        if variantSerializer.is_valid():
            try:
                product = Product.objects.get(pk=request.data["product_id"])
            except:
                return Response(
                {
                    "message": "selected product doesn't exist"
                }, status=status.HTTP_400_BAD_REQUEST
            )
            variant = Variant.objects.create(index=request.data["index"], product=product)
            serializer = VariantSerializer(variant)          
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(variantSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VariantRetrieveUpdateDestroy(APIView):
    permission_classes = (AllowAny, )
    def get_object(self, pk):
        try:
            return Variant.objects.get(pk=pk)
        except Variant.DoesNotExist:
            raise Http404    
    def get(self, request, pk):
        variant = self.get_object(pk)
        serializer = VariantDetailedInfoSerializer(variant)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def put(self, request, pk):
        variant = self.get_object(pk)
        variantSerializer = VariantSerializer(variant, data=request.data, partial=True)
        if variantSerializer.is_valid():
            if request.data.get("product_id") is not None:
                try:
                    product = Product.objects.get(pk=request.data["product_id"])
                except:
                    return Response(
                    {
                        "message": "selected product doesn't exist"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
                variant.product = product
            variantSerializer.save()        
            return Response(variantSerializer.data, status=status.HTTP_201_CREATED)
        return Response(variantSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        variant = self.get_object(pk)
        variant.is_active = False
        variant.save()
        return Response(
            {
                "message": "selected variant is deactivated successfully"
            }, status=status.HTTP_204_NO_CONTENT
        )
        
class MetadataListUpdateDestroy(APIView):
    permission_classes = (AllowAny, )
    def get_object(self, pk):
        try:
            return Variant.objects.get(pk=pk)
        except Variant.DoesNotExist:
            raise Http404    
    def get(self, request, pk):
        variant = self.get_object(pk)
        metadata = variant.metadata.all()        
        serializer = MetadataSerializer(metadata, many=True)          
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        variant = self.get_object(pk)
             
        if request.data.get("metadata") is not None and len(request.data.get("metadata")) >= 1:
            invalid_metadata_info = []
            metadata_doesnot_exist_in_db = []
            metadata = request.data.get("metadata")
            
            for metadata_item in metadata:
                if metadata_item.get("id") is not None:
                    try:
                        metadata_has_id = Metadata.objects.get(pk=metadata_item["id"])
                    except Metadata.DoesNotExist:
                        metadata_doesnot_exist_in_db.append(metadata_item)
                        
                if metadata_item.get("is_deleted") is None:
                    metadataserializer = MetadataSerializer(data=metadata_item)
                    if not metadataserializer.is_valid():
                        invalid_metadata_info.append(
                            {
                                "field": metadata_item["field"],
                                "value": metadata_item["value"]
                            }
                        )
            if len(metadata_doesnot_exist_in_db) > 0:
                return Response(
                    {   
                        "message": "you included metadata ids that doesnot exist in db",
                        "metadata_doesnot_exist_in_db": metadata_doesnot_exist_in_db
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            if len(invalid_metadata_info) > 0:
                return Response(
                    {   
                        "message": "you included invalid metadata info",
                        "invalid_metadata_info": invalid_metadata_info
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            for metadata_item in metadata:
                id = metadata_item.get("id")
                is_deleted = metadata_item.get("is_deleted")
                if id is None:
                    metadata_item_created = Metadata.objects.create(field=metadata_item["field"], value=metadata_item["value"], index=metadata_item["index"], variant=variant)
                elif id is not None and is_deleted is not None and is_deleted == True:
                    metadata_item_deactivated =  Metadata.objects.get(pk=metadata_item["id"])
                    metadata_item_deactivated.is_active = False
                    metadata_item_deactivated.save()
                elif id is not None and is_deleted is None:
                    metadata_item_updated = Metadata.objects.get(pk=id)
                    metadataSerializer = MetadataSerializer(metadata_item_updated, data=metadata_item, partial=True)
                    if metadataSerializer.is_valid():
                        metadataSerializer.save() 
                           
            return Response(MetadataSerializer(variant.metadata.all(), many=True).data, status=status.HTTP_200_OK)    
        return Response(
            {
                "message": "You didn't change any metadata"
            }, status=status.HTTP_200_OK
        )
          
        
        
        
        
        
class MediaCreateUpdateDestroy(APIView):
    permission_classes = (AllowAny, )
    def get_object(self, pk):
        try:
            return Variant.objects.get(pk=pk)
        except Variant.DoesNotExist:
            raise Http404    
    def post(self, request, pk):
        variant = self.get_object(pk)
        mediaSerializer = MediaSerializer(data=request.data, partial=True)
        if mediaSerializer.is_valid():
            file = request.data.get("file")
            client=boto3.client("s3", aws_access_key_id= settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
            # s3 does not need region
            # region_name=os.environ.get(AWS_REGION_NAME),
            )
            file_path = f"image/products/{generateUniqueFileName(file.name)}"
            try:
                # Upload the image to S3
                client.upload_fileobj(file,settings.AWS_STORAGE_BUCKET_NAME,file_path, {'ContentType': "image/png"})
                
                # Return the S3 URL
                s3_url = f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_path}'
                
                media = Media.objects.create(index=request.data["index"], url=s3_url, variant=variant)
                serializer = MediaSerializer(media) 
                         
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)          
            
        return Response(mediaSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, pk):
        media = Media.objects.get(pk=request.data.get("id"))
        mediaSerializer = MediaSerializer(media, data=request.data, partial=True)
        if mediaSerializer.is_valid():
            mediaSerializer.save()  
            return Response(mediaSerializer.data, status=status.HTTP_201_CREATED)
        return Response(mediaSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        media = Media.objects.get(pk=request.data.get("id"))
        media.is_active = False
        media.save()
        return Response(
            {
                "message": "selected media is deactivated successfully",
                "media": MediaSerializer(media).data
            }, status=status.HTTP_204_NO_CONTENT
        )
        
class FileUploadView(APIView):
    permission_classes = (AllowAny, )
    
    def post(self, request):
        name = request.data.get("name")
        file = request.data.get("file")
        
        client=boto3.client("s3", aws_access_key_id= settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
            # s3 does not need region
            # region_name=os.environ.get(AWS_REGION_NAME),
        )
        file_path = f"image/products/{generateUniqueFileName(name)}"

        # response = client.upload_fileobj(file,settings.AWS_STORAGE_BUCKET_NAME,file_path, {'ContentType': "image/png"})
        
        try:
            # Upload the image to S3
            client.upload_fileobj(file,settings.AWS_STORAGE_BUCKET_NAME,file_path, {'ContentType': "image/png"})
            
            # Return the S3 URL
            s3_url = f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_path}'
            return Response({'url': s3_url}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        

        
class InventoryCreateUpdateDestroy(APIView):
    permission_classes = (AllowAny, )
    def get_object(self, pk):
        try:
            return Variant.objects.get(pk=pk)
        except Variant.DoesNotExist:
            raise Http404    
    def post(self, request, pk):
        variant = self.get_object(pk)
        inventorySerializer = InventorySerializer(data=request.data)
        try:
            inventory_exist = Inventory.objects.get(pk=pk)
        except:
            inventory_exist = None
        if inventory_exist is not None:
            return Response(
            {
                "message": "inventory for this variant already exists",
            }, status=status.HTTP_400_BAD_REQUEST
        )
        if inventorySerializer.is_valid():
            inventory = Inventory.objects.create(**inventorySerializer.validated_data, variant=variant)
            serializer = InventorySerializer(inventory)          
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(inventorySerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, pk):
        inventory = Inventory.objects.get(pk=pk)
        inventorySerializer = InventorySerializer(inventory, data=request.data, partial=True)
        if inventorySerializer.is_valid():
            inventorySerializer.save()  
            return Response(inventorySerializer.data, status=status.HTTP_201_CREATED)
        return Response(inventorySerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        inventory = Inventory.objects.get(pk=pk)
        inventory.is_active = False
        inventory.save()
        return Response(
            {
                "message": "selected inventory is deactivated successfully",
                "inventory": InventorySerializer(inventory).data
            }, status=status.HTTP_204_NO_CONTENT
        )
        
class ShippingCreateUpdateDestroy(APIView):
    permission_classes = (IsAdminUser, )
    def get_object(self, pk):
        try:
            return Variant.objects.get(pk=pk)
        except Variant.DoesNotExist:
            raise Http404    
    def post(self, request, pk):
        variant = self.get_object(pk)
        shippingSerializer = ShippingSerializer(data=request.data)
        try:
            shipping_exist = Shipping.objects.get(pk=pk)
        except:
            shipping_exist = None
        if shipping_exist is not None:
            return Response(
            {
                "message": "Shipping for this variant already exists",
            }, status=status.HTTP_400_BAD_REQUEST
        )
        if shippingSerializer.is_valid():
            shipping = Shipping.objects.create(**shippingSerializer.validated_data, variant=variant)
            serializer = ShippingSerializer(shipping)          
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(shippingSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, pk):
        shipping = Shipping.objects.get(pk=pk)
        shippingSerializer = ShippingSerializer(shipping, data=request.data, partial=True)
        if shippingSerializer.is_valid():
            shippingSerializer.save()  
            return Response(shippingSerializer.data, status=status.HTTP_201_CREATED)
        return Response(shippingSerializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        shipping = Shipping.objects.get(pk=pk)
        shipping.delete()
        return Response(
            {
                "message": "selected Shipping is deleted successfully",
            }, status=status.HTTP_204_NO_CONTENT
        )