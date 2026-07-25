
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Item
from .serializers import ItemSerializer
from .functions import get_related_items

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules 



# Create your views here.
class ItemViewSet(ReadOnlyModelViewSet):
    
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    lookup_field = 'name'

    filter_backends = [SearchFilter, OrderingFilter]
    filterset_fields = ['name']
    ordering_fields = ['price']
    

    def retrieve(self, request, name):

        # Get related items
        queryset = get_related_items(name, self.queryset)

        # Serialize the data
        serializer = self.serializer_class(queryset, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    

# Metric Adjusting View
class AprioriView(APIView):
     
    def post(self, request, min_support, metric_name, metric_min_value):

        if not settings.APRIORI_TUNING_ENABLED:
            return Response(
                {"detail": "Live re-fitting is disabled on this deployment: it needs the raw transaction "
                            "data, which isn't published here (see README > Known limitations). Clone the "
                            "repo, supply your own copy of the dataset, and run it locally to use this "
                            "endpoint."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        csv_dir = settings.BASE_DIR / "AprioriAPI" / "static" / "AprioriAPI" / "CSVs"

        # Building the model 
        basket_UK = pd.read_csv(csv_dir / "UK_Transactions.csv.gz",
                                 delimiter=';', index_col="BillNo")
        frq_items = apriori(basket_UK, min_support = min_support, use_colnames = True, low_memory=True)

        # Collecting the inferred rules in a dataframe 
        rules = None
        if metric_name == 'lift':
            rules = association_rules(frq_items, metric ="lift", min_threshold = metric_min_value) 

        elif metric_name == 'confidence':
            rules = association_rules(frq_items, metric ="confidence", min_threshold = metric_min_value)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Sort the rules in descending order by confidence first and lift second
        rules = rules.sort_values(['confidence', 'lift'], ascending = [False, False])

        # Save the rules
        rules.to_pickle(csv_dir / "pickles" / "association_rules2")

        return Response(status=status.HTTP_200_OK)
