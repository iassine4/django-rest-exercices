from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from shop.models import Category
from shop.serializers import CategorySerializer


class CategoryView(APIView):

    def get(self, *args, **kwargs):
        queryset = Category.objects.all()
        serializer = CategorySerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
