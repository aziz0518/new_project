from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.exceptions import ValidationError

class Author(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authors')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



class Book(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    published_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books')

    def clean(self):
        
        if self.published_date and self.author and self.author.birth_date:
            if self.published_date < self.author.birth_date:
                raise ValidationError("Nashr sanasi muallif tug‘ilgan sanasidan oldin bo‘lishi mumkin emas.")

        
        if self.price is not None and self.price < Decimal("0.00"):
            raise ValidationError("Narx manfiy bo‘lishi mumkin emas.")

        
        if self.title and len(self.title) < 3:
            raise ValidationError("Sarlavha uzunligi kamida 3 ta belgidan iborat bo‘lishi kerak.")

    def __str__(self):
        return self.title
