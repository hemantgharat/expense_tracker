from rest_framework import serializers
from expenses.models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'first_name', 'last_name', 'username']
        
# from djoser.user_serializers import UserSerializer, UserCreateSerializer as BaseUserSerializer

# class UserCreateSerializer(BaseUserSerializer):
#     class Meta(BaseUserSerializer.Meta):
#         fields = ['id', 'email', 'username', 'password']