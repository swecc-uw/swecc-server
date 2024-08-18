from rest_framework import serializers
from members.models import Member

class DirectoryMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    linkedin = serializers.SerializerMethodField()
    github = serializers.SerializerMethodField()
    leetcode = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = "__all__"

    def get_social_field(self, obj, field_name):
        field = getattr(obj, field_name)
        if isinstance(field, dict) and not field.get('isPrivate', True):
            return {k: v for k, v in field.items() if k != 'isPrivate'}
        return None

    def get_linkedin(self, obj):
        return self.get_social_field(obj, 'linkedin')

    def get_github(self, obj):
        return self.get_social_field(obj, 'github')

    def get_leetcode(self, obj):
        return self.get_social_field(obj, 'leetcode')

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # remove empty fields
        for field in instance._meta.get_fields():
            field = field.name
            if representation[field] is None or representation[field] == {} or representation[field] == [] or representation[field] == '':
                representation.pop(field)

        return representation