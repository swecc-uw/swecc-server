from rest_framework import serializers
from .models import Member

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        exclude = ['user'] # exclude so we can create a member without user

    def create(self, validated_data):
        user = self.context['request'].user
        print('user', user)
        return Member.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance