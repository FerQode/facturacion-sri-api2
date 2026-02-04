from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..serializers.usuario_serializers import UserProfileSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # request.user es el usuario extraído del Token por DRF
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)
