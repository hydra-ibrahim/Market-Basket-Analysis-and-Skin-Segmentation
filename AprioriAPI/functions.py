
import json
import pandas as pd
from django.conf import settings


def build_consequents_map(rules):
        """Precompute {single-item antecedent: [consequent items]} from a mined rules DataFrame.
        This is the only shape get_related_items() actually needs -- turning a per-request DataFrame
        scan into an O(1) dict lookup, and just as importantly, removing any dependency on unpickling
        pandas/numpy objects at request time, which is fragile across library versions (a committed
        pickle created by one numpy version can fail to load under another -- see DEPLOY.md)."""

        single_antecedent = rules[rules['antecedents'].apply(lambda x: len(x) == 1)].copy()
        single_antecedent['antecedent_item'] = single_antecedent['antecedents'].apply(lambda x: next(iter(x)))

        return {
            item: group['consequents'].explode().unique().tolist()
            for item, group in single_antecedent.groupby('antecedent_item')
        }


def get_related_items(item, queryset):

        # Load the precomputed {item: [consequents]} map -- plain JSON, no pandas/numpy involved in
        # reading it, so nothing here can go version-stale the way the old pickle-based approach did.
        map_path = settings.BASE_DIR / "AprioriAPI" / "static" / "AprioriAPI" / "CSVs" / "pickles" / "consequents_map.json"
        with open(map_path, encoding='utf-8') as f:
            consequents_map = json.load(f)

        consequents = consequents_map.get(item, [])

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
