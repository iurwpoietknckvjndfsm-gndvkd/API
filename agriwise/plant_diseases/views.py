from rest_framework import generics, permissions, status
from rest_framework.response import Response

from agriwise.plant_diseases.permissions import IsOwnerOrReadOnly
from agriwise.users.models import User

from .ml_model.plant_diseases import mobile_net
from .models import PlantDisease
from .serializers import PlantDiseaseSerializer, PlantImageSerializer


class PlantDiseasePost(generics.CreateAPIView):

    serializer_class = PlantImageSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            uploaded_file = serializer.data["image"]
            disease = mobile_net().compute_prediction(uploaded_file)
            plant_disease_serializer = PlantDiseaseSerializer(data={"disease": disease})
            user = User.objects.filter(id=request.user.id).first()
            if plant_disease_serializer.is_valid():
                plant_disease_serializer.save(
                    plant_image=serializer.instance, user=user, disease=disease
                )
                return Response(
                    plant_disease_serializer.data, status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    plant_disease_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlantDiseaseList(generics.ListAPIView):
    serializer_class = PlantDiseaseSerializer
    queryset = PlantDisease.objects.select_related("plant_image").all()


class PlantDiseaseRetrieveDestroy(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    serializer_class = PlantDiseaseSerializer
    queryset = PlantDisease.objects.all()
    lookup_field = "id"

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Plant disease instance deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
