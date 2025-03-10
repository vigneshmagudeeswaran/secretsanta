from django.forms import ValidationError
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from Employee.models import Employee, SecretSanta
from Employee.serializers import EmployeeSerializer, SecretSantaFileSerializer, SecretSantaSerializer,EmployeeFileSerializer
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from backend.utils import SecretSantaUtils,EmployeeUtils
import random
import pandas as pd
from collections import defaultdict



class EmployeeViewSet(ViewSet):
    queryset =Employee.objects.all()
    def list(self, request):
        employees = self.queryset
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        employee = self.queryset.get(pk=pk)
        serializer = EmployeeSerializer(employee)
        return Response(serializer.data)

    def create(self, request):        
        serializer = EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):     
        employee = self.queryset.get(pk=pk)
        serializer = EmployeeSerializer(employee, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'],url_path='upload',parser_classes=[MultiPartParser, FormParser])
    def employees_upload(self, request):
        file = request.FILES.get('file')
        serializer = EmployeeFileSerializer(data=request.data, context={'file': file})
        
        if serializer.is_valid():
            serializer.save()
            print(dir(serializer))
            print(serializer.error_messages)
            print(serializer.errors)
            return Response({'new employees loaded succesfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SecretSantaViewSet(ViewSet):
    
    queryset = SecretSanta.objects.all()
    
    def list(self, request):
        secret_santas = self.get_queryset()
        serializer = SecretSantaSerializer(secret_santas, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None): 
        try:       
            secret_santa = self.get_queryset()
            serializer = SecretSantaSerializer(secret_santa)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "secretsanta not found."}, status=status.HTTP_404_NOT_FOUND)  
          

    def create(self, request):        
        serializer = SecretSantaSerializer(data=request.data)
        try:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                # For non-field errors, extract messages under '__all__'
                errors = e.message_dict.get('__all__', [])
            else:
                # For single error messages, convert to a list
                errors = [str(e)]
            return Response({'error' : errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):        
        secret_santa = self.get_queryset()
        serializer = SecretSantaSerializer(secret_santa, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    
    @action(detail=False, methods=['post'],url_path='upload',parser_classes=[MultiPartParser, FormParser])
    def secret_santa_upload(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file was provided"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            serializer =SecretSantaFileSerializer(data=request.data,context={'file':file})
            if serializer.is_valid():
                serializer.save()
            return Response({"message":"new secret childs loaded"},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_queryset(self):
        if self.action == 'list':
            queryset = SecretSanta.objects.all()
        elif self.action == 'retrieve':
            pk = self.kwargs.get('pk')
            queryset = SecretSanta.objects.get(pk=pk)
            print(queryset)
        elif self.action == 'update':
            pk = self.kwargs.get('pk')
            queryset = SecretSanta.objects.get(pk=pk)
        else:
            queryset = SecretSanta.objects.all()
        
        return queryset
        
    @action(detail=False, methods=['get'],url_path='generate')      
    def generate_new_santa_csv(self,request):
        year = request.GET.get('year')
        print(year)
        queryset_lastyear= SecretSanta.objects.filter(year=int(year)-1)
        queryset_current_year= SecretSanta.objects.filter(year=int(year))
        employees = Employee.objects.all()
        available_secret_children = [employee.id for employee in employees]
        print(available_secret_children)
        employee_dont_have_children = [employee.id for employee in employees]
        
        employee_secret_child_set = set()
        csv_dict = defaultdict(list)
        count=0
        for employee_id in employee_dont_have_children[:]:
            count=count+1
            print(f'for loop iteration count{count}')
            assigned_children = False
            
            while not assigned_children:
                
                child_id= random.choice(available_secret_children)
                print(child_id)
                if employee_id == child_id:
                    print('employeeid and child id is same')
                    continue
                employee= employees.get(id=employee_id)
                
                print(employee)
                prev_year_child = employee.secret_santa.get(year=int(year)-1).id
                print(prev_year_child)
                if child_id != prev_year_child:
                    employee_secret_child_set.add((employee_id,child_id,year))
                    child = employees.get(id=child_id)
                    csv_dict['Employee_Name'].append(employee.name)
                    csv_dict['Employee_EmailID'].append(employee.email)
                    csv_dict['Secret_Child_Name'].append(child.name)
                    csv_dict['Secret_Child_EmailID'].append(child.email)
                    csv_dict['child_id'].append(child_id)
                    csv_dict['employee_id'].append(employee_id)
                    csv_dict['previous_year_child_id'].append(prev_year_child)
                    
                    available_secret_children.remove(child_id)
                    employee_dont_have_children.remove(employee_id)
                    assigned_children = True

        df = pd.DataFrame(csv_dict)
        df.to_csv("secretsanta_pairs.csv", index=False)
        return Response({"message":csv_dict},status=status.HTTP_200_OK)
                    
                
                
                
                
            
            
            
            
            
        
        
        
        
        
        
    
    
