from rest_framework.serializers import ModelSerializer, HyperlinkedModelSerializer

from .models import Item

class ItemSerializer(ModelSerializer
    # HyperlinkedModelSerializer
    ):

    class Meta:

        model = Item
        fields = ['name', 'price']
