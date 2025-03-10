from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    def __str__(self):
        return self.name

class SecretSanta(models.Model):
    employee = models.ForeignKey(Employee,related_name='employee', on_delete=models.CASCADE)
    secret_santa = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='secret_santa')
    year = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ('employee','secret_santa')
    
    def clean(self):
        # Ensure the employee can't choose themselves
        
        if self.employee == self.secret_santa:
            raise ValidationError("An employee cannot choose themselves as Secret Santa.")
        
        # Ensure the employee hasn't chosen the same person last year
        last_year = self.year - 1
        last_year_secret_santa = SecretSanta.objects.filter(employee=self.employee, year=last_year, secret_santa=self.secret_santa)
        
        if last_year_secret_santa.exists():
            raise ValidationError(f"You can't choose {self.secret_santa.name} again as your Secret Santa from last year.")
        
    def save(self,*args,**kwargs):
        self.full_clean()
        super().save(*args,**kwargs)
        
    def __str__(self):
        return f"{self.employee.name} -> {self.secret_santa.name} ({self.year})"