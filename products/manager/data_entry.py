from products.models import (
    Product,
    Variant,
    Metadata,
    Media,
    Inventory,
)
from products.serializers import(
    VariantDetailedInfoSerializer,
)

from django.conf import settings
import boto3
from products.utils import (
    generateUniqueFileName,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from django.http import JsonResponse
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import re
import math


def fc_is_integerable(input_string):
    if input_string is None:
        return False
    try:
        # Try converting the string to an integer
        int_value = int(input_string)
        return True
    except ValueError:
        # If ValueError occurs, the string is not integerable
        return False
def fc_get_id_from_row(row):
    id = None
    if row.get("Product id") is not None:
        id = row.get("Product id")
    elif row.get("productid") is not None:
        id = row.get("productid")
    return id
def fc_get_rows_from_sheet(url):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(settings.GOOGLE_SERVICE_ACCOUNT_CREDENTIALS, scope)
    

    client = gspread.authorize(creds)

    # Open the Google Sheet by URL
    sheet = client.open_by_url(url)

    sheet_instance = sheet.get_worksheet(0)
    
    rows = sheet_instance.get_all_records()
    
    return rows


def fc_upload_file_to_s3(drive_service, file, variant):
    request = drive_service.files().get_media(fileId=file.get("id"))
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        
    client=boto3.client("s3", aws_access_key_id= settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
    )
    file_path = f"image/test/{generateUniqueFileName(file.get('name'))}"
    fh.seek(0)
    # print(fh.getvalue())
    try:
        # Upload the image to S3
        client.upload_fileobj(fh,settings.AWS_STORAGE_BUCKET_NAME, file_path, {'ContentType': "image/webp"})
        
        # Return the S3 URL
        s3_url = f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_path}'
        # return Response({'url': s3_url}, status=status.HTTP_201_CREATED)
        media = Media.objects.filter(variant=variant)
        # media_index = 1
        # if len(media) > 0:
        #     media_index = media[len(media) - 1].index + 1
        Media.objects.create(variant=variant, index=int(file.get("name").split(".")[0]), url=s3_url)
        
    except Exception as e:
        # return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        print("err:", str(e))
        
def fc_get_all_folders_in_folder(folder_id):
    folders = []
    
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(settings.GOOGLE_SERVICE_ACCOUNT_CREDENTIALS, scope)
    drive_service = build('drive', 'v3', credentials=creds)
    
    file_metadata = drive_service.files().get(fileId=folder_id).execute()

    # Check if the file is a folder
    if 'folder' not in file_metadata['mimeType']:
        return JsonResponse({'error': 'The specified file ID is not a folder.'}, status=400)

    def recursively_list_folders(page_token=None):
        folder_contents = drive_service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
            fields="nextPageToken, files(name, id)",
            pageToken=page_token
        ).execute()

        folders.extend([{'name': item['name'], 'id': item['id']} for item in folder_contents.get('files', [])])

        next_page_token = folder_contents.get('nextPageToken')
        if next_page_token:
            recursively_list_folders(page_token=next_page_token)

    recursively_list_folders()
    return {
        "drive_service": drive_service,
        "folders": folders
    }


def fc_create_media_for_variant(sub_folder_id, drive_service, variant):
    try: 
        sub_folder_contents = drive_service.files().list(q=f"'{sub_folder_id}' in parents").execute()
        
        
        media_files = [{'name': item['name'], 'id': item['id']} for item in sub_folder_contents.get('files', [])]
        # print(media_files)
        for media_file in media_files:
            fc_upload_file_to_s3(drive_service, media_file, variant)

    except Exception as e:
        # Handle errors appropriately
        print(str(e))
        # return JsonResponse({'error': str(e)}, status=500)

def fc_create_metadata_from_string(variant, value):
    if len(value.split("=")) > 1:
        field = value.split("=")[0]
        field_value = value.split("=")[1].replace('"', '')
        metadata = Metadata.objects.filter(variant=variant)
        metadata_item_index = 1
        if len(metadata) > 0:
            metadata_item_index = metadata[len(metadata) - 1].index + 1   
        new_metadata_item = dict()
        new_metadata_item["variant"] = variant
        new_metadata_item["index"] = metadata_item_index
        new_metadata_item["value"] = field_value
        if field != "null":
            new_metadata_item["field"] = field
        if field == "Description":
            product = variant.product
            if product.description is None:
                product.description = value
                product.save() 
        else:
            metadata_item = Metadata.objects.create(**new_metadata_item)
               
def fc_get_id_from_row(row):
    if row.get("product id") is not None:
        return row.get("product id")
    elif row.get("Product id") is not None:
        return row.get("Product id")
    elif row.get("productid") is not None:
        return row.get("productid")
    else:
        return None
def fc_get_name_from_row(row):
    name = None
    if row.get("Name") is not None:
        name = row.get("Name")
        if len(name.split("=")) > 1:
            name = name.split('"')[1]
    elif row.get("name") is not None:
        name = row.get("name")
    return name
def fc_get_inventory_data_from_row(row):
    result = dict()
    price = None
    currency = None
    if row.get("Price") is not None:
        price = str(row.get("Price"))
    elif row.get("price") is not None:
        price = str(row.get("price"))
    if len(price.split("=")) > 1:
        price = price.split('"')[1]
    elif len(price.split('"')) > 1:
        price = price.split('"')[1]
    if row.get("currency") is not None:
        currency = row.get("currency")
    if row.get("Currency") is not None:
        currency = row.get("Currency")
    if price is not None and price != "":
        try:
            result["price"] = math.floor(float(price.replace(",", "")))
        except:
            pass
    if currency is not None:
        result["currency"] = currency
    return result

def fc_product_entry_by_row(row, sub_folder_id, drive_service): 
            
    name = fc_get_name_from_row(row)
    source_url = row["sourceurl"]
    product = None
    
    try:
        product = Product.objects.get(name=name)
    except:
        product = None
    if product is None:
        product = Product.objects.create(name=name, source_url=source_url)  
        
    variants = Variant.objects.filter(product=product)
    variant_index = 1
    if len(variants) > 0:
        variant_index = variants[len(variants) - 1].index + 1        
    variant = Variant.objects.create(product=product, index=variant_index)
    
    new_inventory_data = fc_get_inventory_data_from_row(row)        
    inventory = Inventory.objects.create(variant=variant, **new_inventory_data)
    unecessary_keys = [
        "product id", "Product id", "productid", 
        "sourceurl", 
        "Name", "name", 
        "soldout", "Soldout",
        "price", "Price",
        "currency", "Currency",
        "type", "Type"
    ]
    for key, value in row.items():
        if key in unecessary_keys:
            pass
        else:
            if value != "":
                if key == "Measurements":
                    multi_metafield_data = value.split(":")[1].split(",") 
                    for metafield_item_data in multi_metafield_data:
                        fc_create_metadata_from_string(variant, metafield_item_data.strip())
                else:
                    fc_create_metadata_from_string(variant, value)
            
    if sub_folder_id is not None:
        fc_create_media_for_variant(sub_folder_id, drive_service, variant)
