from rest_framework import serializers
from django.utils import timezone
from .models import Author, Book

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'user', 'first_name', 'last_name', 'birth_date']
        read_only_fields = ['user']

    def validate_birth_date(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Tug‘ilgan sana kelajakda bo‘lishi mumkin emas.")
        return value

class BookSerializer(serializers.ModelSerializer):
    author_full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'description', 'author', 'price', 'published_date', 'created_by', 'author_full_name']
        read_only_fields = ['created_by', 'author_full_name']

    def get_author_full_name(self, obj):
        return f"{obj.author.first_name} {obj.author.last_name}"

    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Sarlavha uzunligi kamida 3 ta belgidan iborat bo‘lishi kerak.")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Narx manfiy bo‘lishi mumkin emas.")
        return value

    def validate(self, data):
        author = data.get('author')
        published_date = data.get('published_date')
        if author and published_date:
            if published_date < author.birth_date:
                raise serializers.ValidationError("Nashr sanasi muallif tug‘ilgan sanasidan oldin bo‘lishi mumkin emas.")
        return data

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
