from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model


class CustomUserSerializer(UserSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "phone",
        ]
        read_only_fields = ["id"]
