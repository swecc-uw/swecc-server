from rest_framework import serializers
from .models import AttendanceSession
from members.models import User

class AttendanceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSession
        fields = '__all__' 

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id']