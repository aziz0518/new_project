from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
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




class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                data['user'] = user
            else:
                raise serializers.ValidationError("Login yoki parol noto‘g‘ri")
        else:
            raise serializers.ValidationError("Har ikkala maydon ham to‘ldirilishi kerak")

        return data
