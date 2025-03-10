import subprocess
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()   

employee_list_excel_path =os.getenv("employee_list_excel_path")
last_yearsecret_santa_excel= os.getenv("last_yearsecret_santa_excel")

# Define the URL
url = 'http://127.0.0.1:8000/api/employee/upload/'

# Define the file to upload
employee_list_path = 'F:/Employee-List.xlsx'

def upload_excel(path,url):
    with open(path , 'rb') as file:
        response = requests.post(url, files={'file': file})

upload_excel(employee_list_excel_path,'http://127.0.0.1:8000/api/employee/upload/')
upload_excel(last_yearsecret_santa_excel,'http://127.0.0.1:8000/api/secretsanta/upload/')


resp = requests.get(url='http://127.0.0.1:8000/api/secretsanta/generate/?year=2024')

print(resp.text)