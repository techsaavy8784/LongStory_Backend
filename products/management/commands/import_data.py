from django.core.management.base import BaseCommand
from django.utils import timezone
from products.manager.data_entry import (
    fc_get_rows_from_sheet,
    fc_product_entry_by_row,
    fc_get_id_from_row,
    fc_is_integerable,
    fc_get_all_folders_in_folder
)

class Command(BaseCommand):
    help = 'import variant data from google diver'

    def add_arguments(self, parser):        
        parser.add_argument('-s', '--sheet_url', type=str, help='input a google sheet url', )
        parser.add_argument('-f', '--folder_id', type=str, help='input a google drive file id', )
    
    def handle(self, *args, **kwargs):
        sheet_url = kwargs['sheet_url']
        folder_id = kwargs['folder_id']
        url1 = "https://docs.google.com/spreadsheets/d/1mSZ-x3kkxUYkdyiFga2ibAywId73ZebI5lzSa7DYOaA/edit#gid=1784093875"
        url21 = "https://docs.google.com/spreadsheets/d/1wLxssxVq9E55VAAVznvgFR0cQGMndnI4en-sC88eMGk/edit#gid=1464251853"       
        url22 = "https://docs.google.com/spreadsheets/d/1v15O4S5kT4mkPt8mPD9pYQFIz5Q8KzwbcxXuKedscUs/edit#gid=0"  
        folder_id = "1PA_RJhjisD_LE4pmEAV32yEN0aNT3ipd"        
        # sheet_url = url22       
        
        
        try:
            self.stdout.write('----Start fetching data from google sheet')
            result = fc_get_all_folders_in_folder(folder_id)
            folders = result["folders"]
            drive_service = result["drive_service"]
            rows = fc_get_rows_from_sheet(sheet_url)
            self.stdout.write(self.style.SUCCESS('----Fetched "%d" variants from google sheet successfully!' % len(rows)))        
            print(len(folders))
            count = 1
            for row in rows:             
                id = fc_get_id_from_row(row)
                if fc_is_integerable(id):
                    sub_folder_id = None
                    sub_folders = [folder for folder in folders if folder.get("name") == str(id)]
                    print(sub_folders)
                    if len(sub_folders) > 0:
                        sub_folder_id = sub_folders[0].get("id")    
                    self.stdout.write('"%d"----Start writing variant for index "%d" to db' % (count, id) )
                    fc_product_entry_by_row(row, sub_folder_id, drive_service)
                    self.stdout.write(self.style.SUCCESS('----wrote variant for index "%d" to db successfully!' % id))                                     
                    count += 1
                    
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('Command execution interrupted'))
            
            