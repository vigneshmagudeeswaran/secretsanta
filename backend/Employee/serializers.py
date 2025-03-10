from django.forms import ValidationError
from rest_framework import serializers
from .models import Employee,SecretSanta
import pandas as pd
from backend.utils import SecretSantaUtils,EmployeeUtils


class SecretSantaSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False)
    class Meta:
        model = SecretSanta
        fields = '__all__'
    def __init__(self, *args, **kwargs):
    
        file = kwargs.get('context', {}).get('file', None)
        if file:
            self.Meta.fields = ['file']
        
        super().__init__(*args, **kwargs)
    def handle_csv_upload(self, file):
       
        return SecretSantaUtils().file_upload(file)
        
    def save(self, *args, **kwargs):
        
        file = self.context.get('file', None)
        if file:
            return self.handle_csv_upload(file)
        else:
            
            return super().save(*args, **kwargs)
        
class SecretSantaFileSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    def handle_csv_upload(self, file):
        return SecretSantaUtils().file_upload(file)
        
    def save(self, *args, **kwargs):
        
        file = self.context.get('file', None)
        if file:
            return self.handle_csv_upload(file)
        else:
            
            return super().save(*args, **kwargs)

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'   

class EmployeeFileSerializer(serializers.Serializer):
    
    file = serializers.FileField()

    def handle_csv_upload(self, file):
       
       return EmployeeUtils().file_upload(file)
    
    def save(self, *args, **kwargs):
        
        file = self.context.get('file', None)
        if file:
            return self.handle_csv_upload(file)
        else:
            
            return super().save(*args, **kwargs)