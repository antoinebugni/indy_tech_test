from rest_framework.routers import SimpleRouter

from .views import PromoCodeViewSet

promocodes_router = SimpleRouter()

promocodes_router.register(r'promocodes', PromoCodeViewSet)
