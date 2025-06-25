from rest_framework import serializers
from django.contrib.auth.models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
    
    def validate(self, attrs):
        user_exist = User.objects.filter(
            username=attrs['username']
        )
        if user_exist.exists():
            raise serializers.ValidationError({'error': f"username {attrs['username']} already existed"})
        return super().validate(attrs)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user
