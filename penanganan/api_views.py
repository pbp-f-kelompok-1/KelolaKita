from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Pemeriksaan
from .serializers import PemeriksaanSerializer


@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def pemeriksaan_list(request):
    if request.method == "GET":
        pemeriksaan = Pemeriksaan.objects.all()
        serializer = PemeriksaanSerializer(pemeriksaan, many=True)
        return Response(serializer.data)

    serializer = PemeriksaanSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(pengguna=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def pemeriksaan_detail(request, pk):
    pemeriksaan = get_object_or_404(Pemeriksaan, pk=pk)

    if request.method == "GET":
        serializer = PemeriksaanSerializer(pemeriksaan)
        return Response(serializer.data)

    if request.method == "PUT":
        serializer = PemeriksaanSerializer(pemeriksaan, data=request.data)
    elif request.method == "PATCH":
        serializer = PemeriksaanSerializer(
            pemeriksaan,
            data=request.data,
            partial=True,
        )
    else:
        pemeriksaan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)