from rest_framework import serializers

from .models import PromoCode


class PromoCodeReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = (
            'uuid',
            'name',
            'advantage',
            'restrictions',
        )
        read_only_fields = (
            'uuid',
            'name',
            'advantage',
            'restrictions',
        )


class PromoCodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = (
            'name',
            'advantage',
            'restrictions',
        )


class PromoCodeValidateSerializer(serializers.Serializer):
    promocode_name = serializers.CharField(max_length=255)
    arguments = serializers.JSONField()
