from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Member

User = get_user_model()
class MemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Member
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user
        return Member.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance