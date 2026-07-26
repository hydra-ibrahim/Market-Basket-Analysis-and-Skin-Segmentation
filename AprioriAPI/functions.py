
import pandas as pd
from django.conf import settings


def get_related_items(item, queryset):

        # Load association rules
        rules_path = settings.BASE_DIR / "AprioriAPI" / "static" / "AprioriAPI" / "CSVs" / "pickles" / "association_rules2"
        rules = pd.read_pickle(rules_path)

        # Find the consequents
        consequents = rules[rules['antecedents']
                                    .apply(lambda x: 
                                        (item in x) and (len(list(x)) == 1)
                                        )
                            ][['consequents']]                                                            \
                            .explode('consequents')                                                        \
                            .consequents.unique().tolist()

        
        # Get the consequents info
        related_names = list(consequents)

        # If the "consequents" number is less than ten items,
        # complete the recommended items to be ten by the most bought items
        if len(related_names) < 10:

            complementary_num = 10 - len(related_names)
            comp_names = list(
                queryset.exclude(name__in=related_names)
                        .order_by('-quantity')
                        .values_list('name', flat=True)[:complementary_num]
            )
            related_names += comp_names

        return queryset.filter(name__in=related_names)
