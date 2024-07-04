from rest_framework import serializers
from .models import Member

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['member_id', 'created', 'email', 'role', 'first_name', 'last_name', 'preview', 'major', 'grad_date', 'discord_username', 'linkedin', 'github', 'leetcode', 'resume_url', 'local', 'bio', 'discord_id']