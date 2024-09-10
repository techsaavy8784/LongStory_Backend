from products.models import (
    Category,
    Product,
    Variant,
    Metadata,
    Media,
    Inventory,
    Like
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
    ProductDetailedInfoSerializer
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
from products.manager.paginations import ProductPagination


class CategoryListCreate(APIView):
    permission_classes = (AllowAny, )    
    # permission_classes = (IsAdminUser, )    
    def get(self, request):
        
        categories = Category.objects.filter(is_active=True)               
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

class ProductListCreate(APIView):
    permission_classes = (AllowAny, )
    # pagination_class = ProductPagination
    
    def get(self, request):
        filter_params = dict()
        order_by = request.query_params.get("order_by")
        
        if request.query_params.get("desc") is not None and order_by is not None:
            desc = convertToBoolean(request.query_params.get("desc"))
            if desc is not None and desc is True:
                order_by = f"-{order_by}"
        if order_by is None:
            order_by = "-created_at"
                
        if request.query_params.get("is_published") is not None:
            is_published = convertToBoolean(request.query_params.get("is_published"))
            if is_published is not None:
                filter_params["is_published"] = is_published 
                
        filter_params["is_active"] = True
        
        
                             
        products = Product.objects.filter(**filter_params).order_by(order_by)
        
        category_id = request.query_params.get("category_id")
        # get product that followees like
        like = convertToBoolean(request.query_params.get("like"))  
        user = request.user      
        followees = user.followees.all()
        followee_users = [follow.followee for follow in followees]
        followee_users_likes = Like.objects.filter(user__in = followee_users)
        followee_users_like_products = [like.product for like in followee_users_likes]
        products = followee_users_like_products
        if category_id is not None:
            products = products.filter(category__in=[category_id])
            
        if like is True:
            pass
        if request.query_params.get("search") is not None:
            search = request.query_params.get("search")
            products = products.filter(Q(name__icontains=search) | Q(description__icontains=search) | Q(variants__metadata__field__icontains=search) | Q(variants__metadata__value__icontains=search)).distinct()        
                    
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
        productSerializer = ProductSerializer(product, data=request.data, partial=True)
        if productSerializer.is_valid():
            if category_id is not None:
                try:
                    category = Category.objects.get(pk=category_id)
                except:
                    category
                    return Response(
                    {
                        "message": "selected category doesn't exist"
                    }, status=status.HTTP_400_BAD_REQUEST
                )
                product.category = category
            productSerializer.save()        
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
            print("come here")
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
        
        print(settings.AWS_SECRET_ACCESS_KEY)
        
        client=boto3.client("s3", aws_access_key_id= settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
        )
        file_path = f"image/products/{generateUniqueFileName(name)}"
        
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
    
