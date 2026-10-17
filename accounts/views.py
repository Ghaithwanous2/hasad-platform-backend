
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    IdentifierTokenObtainPairSerializer,
)


class IdentifierTokenObtainPairView(TokenObtainPairView):
    serializer_class = IdentifierTokenObtainPairSerializer
