from rest_framework import serializers
from .models import AuthKey

class AuthKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthKey
        fields = '__all__'