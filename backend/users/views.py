from rest_framework import generics, permissions

from .serializers import UserProfileSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """GET / PATCH the current user's profile."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
