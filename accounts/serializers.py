from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.Serializer):

    name = serializers.CharField(min_length=2, max_length=100)
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(min_length=8, max_length=72, write_only=True, trim_whitespace=False)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=72, write_only=True, trim_whitespace=False)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)
    permissions = serializers.ListField(child=serializers.CharField(), source="api_permissions", read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "role", "permissions"]


class AuthResultSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="Bearer JWT")
    user = UserSerializer()


class CurrentUserSerializer(serializers.Serializer):
    user = UserSerializer()
