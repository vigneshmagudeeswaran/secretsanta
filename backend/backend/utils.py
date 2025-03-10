from django.forms import ValidationError
from Employee.models import Employee,SecretSanta
import pandas as pd
from collections import defaultdict
from django.db import IntegrityError, transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

class EmployeeUtils:
   
    def create_secret_santa_object_list(self,**kwargs):
        
        df= kwargs.get('df')
        employees_to_create = []
        employees_to_update = []
        try:
            
            for _, row in df.iterrows():
                name = row.get('Employee_Name')
                email= row.get('Employee_EmailID')
                employee, created = Employee.objects.get_or_create(email=email)
                if created:        
                    employee.name = name
                    employee.email = email
                    employees_to_create.append(employee)
                else:
                    
                    employee.name = name
                    employee.email = email
                    employees_to_update.append(employee)
        
            with transaction.atomic():    
                if employees_to_create:
                    Employee.objects.bulk_create(employees_to_create)

                if employees_to_update:
                    Employee.objects.bulk_update(employees_to_update, fields=['name', 'email']) 
                    
            return True, None      
        
        except IntegrityError as e:
            return False, {"error": "Integrity error occurred while processing data.", "details": str(e)}
        except Exception as e:
            return False, {"error": str(e)}   

      
    def file_upload(self,file):
        try:
            df = pd.read_excel(file)
            
            required_columns = ['Employee_Name', 'Employee_EmailID']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")

            self.create_secret_santa_object_list(df=df)
            
            success, error = self.create_secret_santa_object_list(df=df)
            if not success:
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
            

        except pd.errors.ParserError:
            return Response({"error": "Error parsing Excel file."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SecretSantaUtils:
    def validate_df(self, df, year):
        validated_data = defaultdict(list)
           
        for _, row in df.iterrows():
            prev_santa = SecretSanta.objects.filter(employee__email=row.get('Employee_EmailID'), year=year-1).first()
            is_previous_santa = False
            if prev_santa:
                if prev_santa.secret_santa.email != row.get('Secret_Child_EmailID'):
                    is_previous_santa = False
                else:
                    is_previous_santa = True
            if row.get('Employee_EmailID') != row.get('Secret_Child_EmailID') and not is_previous_santa:
                validated_data['matched'].append(row)
            else:
                validated_data['unmatched'].append(row)
        return validated_data
   
    def create_secret_santa_object_list(self, **kwargs):  
        df = kwargs.get('df')
        year = kwargs.get('year')
        validated_data = self.validate_df(df, year)
        santas_to_create = []
        santas_cannot_create = validated_data['unmatched']
        
        # Keep track of failures due to missing employees
        missing_employees = []
        
        for row in validated_data['matched']:
            try:
                # Try to get both employees
                employee = Employee.objects.get(email=row.get('Employee_EmailID'))
                secret_santa = Employee.objects.get(email=row.get('Secret_Child_EmailID'))
                
                # If both exist, create the Santa pairing
                santas_to_create.append(
                    SecretSanta(
                        employee=employee,
                        secret_santa=secret_santa,
                        year=year
                    )
                )
            except Employee.DoesNotExist:
                # Track which employees don't exist
                missing_employees.append({
                    'employee_email': row.get('Employee_EmailID'),
                    'child_email': row.get('Secret_Child_EmailID'),
                    'error': f"Employee with email {row.get('Employee_EmailID')} or {row.get('Secret_Child_EmailID')} does not exist"
                })
        
        # Log numbers for debugging
        print(f"Validated rows: {len(validated_data['matched'])}")
        print(f"Invalid rows: {len(validated_data['unmatched'])}")
        print(f"Rows with missing employees: {len(missing_employees)}")
        print(f"Final santas to create: {len(santas_to_create)}")
        
        return santas_to_create, santas_cannot_create, missing_employees
     
    def file_upload(self, file):
        try:
            year = int(file.name.split('.')[0].split('-')[-1])
            df = pd.read_excel(file)
           
            required_columns = ['Employee_Name', 'Employee_EmailID', 'Secret_Child_Name', 'Secret_Child_EmailID']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return Response({"error": f"Missing required columns: {', '.join(missing_columns)}"},
                              status=status.HTTP_400_BAD_REQUEST)
                
            santas_to_create, santas_cannot_create, missing_employees = self.create_secret_santa_object_list(df=df, year=year)
            
            # Count them instead of returning the objects directly
            create_count = len(santas_to_create)
            cannot_create_count = len(santas_cannot_create)
            missing_count = len(missing_employees)
            
            # Use transaction to ensure database consistency
            with transaction.atomic():
                if santas_to_create:
                    SecretSanta.objects.bulk_create(santas_to_create)
                    
                    return True,None              
        except pd.errors.ParserError:

            return False,{"error": "Error parsing Excel file."}
        except Exception as e:
            raise ValidationError({"error": f"Error parsing Excel file {e}."})
  