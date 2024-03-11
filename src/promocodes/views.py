from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import PromoCode
from .serializers import PromoCodeReadSerializer, PromoCodeCreateSerializer, PromoCodeValidateSerializer
from .utils import validate_promo_code


class PromoCodeViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for PromoCode model:
    - retrieve
    - create
    - validate
    """

    queryset = PromoCode.objects.all()
    serializers = {
        'default': PromoCodeReadSerializer,
        'create': PromoCodeCreateSerializer,
        'validate': PromoCodeValidateSerializer,
    }
    # TODO : Fix permissions
    permissions = {'default': [AllowAny], 'create': [AllowAny]}

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers['default'])

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except ValueError as e:
            return Response({'error': f'Failed to create promo code: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='validate', url_name='validate')
    def validate(self, instance):
        try:
            promocode_name = self.request.data['promocode_name']
            promocode = PromoCode.objects.get(name=promocode_name)
        except PromoCode.DoesNotExist:
            return Response({'error': f'Promo code {promocode_name} does not exist'}, status=status.HTTP_404_NOT_FOUND)

        arguments = {}
        if 'arguments' in self.request.data:
            arguments = self.request.data['arguments']

        try:
            failure_reasons = validate_promo_code(promocode.restrictions, arguments)
        except ValueError as e:
            return Response({'error': f'Failed to validate promo code: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        if len(failure_reasons) > 0:
            response = {"promocode_name": promocode_name, "status": "denied", "reasons": failure_reasons}
            return Response({'error': response}, status=status.HTTP_400_BAD_REQUEST)

        response = {"promocode_name": promocode_name, "status": "accepted", "advantage": promocode.advantage}
        return Response({'message': response}, status=status.HTTP_200_OK)
