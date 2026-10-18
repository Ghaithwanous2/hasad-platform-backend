
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserMeSerializer

from .serializers import (
    IdentifierTokenObtainPairSerializer,
)


class IdentifierTokenObtainPairView(TokenObtainPairView):
    serializer_class = IdentifierTokenObtainPairSerializer



from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserMeSerializer


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)
