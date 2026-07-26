# Market Basket Analysis and Skin Segmentation

A Django REST API combining two independent machine learning pipelines: an Apriori-based product recommendation engine for an e-commerce inventory derived from real transaction data, and a k-Nearest Neighbours skin-pixel classifier served through a browser canvas interface.

Built as my course project (Information Systems Engineering) in Informatics Engineering at Tishreen University, 2024. All design, implementation, and analysis in this repository is my own work.

## Try it online

The application is publicly available through GitHub Pages:

**https://hydra-ibrahim.github.io/Market-Basket-Analysis-and-Skin-Segmentation/**

The landing page provides access to both the Market Basket Analysis and Skin Segmentation demos.

## Contents

- [Overview](#overview)
- [Notes](#notes)
- [Project structure](#project-structure)
- [Setup](#setup)
- [API reference](#api-reference)
- [Datasets](#datasets)
- [k-NN model selection](#k-nn-model-selection)
- [Data preparation](#data-preparation)
- [Association rules](#association-rules)
- [Known limitations](#known-limitations)
- [References](#references)
- [License](#license)

## Overview

Two independent Django apps sit behind a single REST API.

**`AprioriAPI`** mines association rules from a UK online-retail transaction history using the Apriori algorithm (via `mlxtend`), then serves up to ten related-item recommendations for a given product. If fewer than ten rule-based matches exist for an item, the recommendation list is topped up with the store's best-selling items.

**`KNNAPI`** classifies a single R/G/B pixel as skin or non-skin using a k-Nearest Neighbours classifier (`scikit-learn`), trained on the UCI Skin Segmentation dataset. A canvas-based frontend page lets a user click a pixel on an uploaded image and get a live prediction.

Both apps also expose a parameter-adjustment endpoint that re-fits the underlying model (Apriori support/metric thresholds, or `k` for the classifier) and persists the result to disk.

## Notes

An earlier version of `KNNView.get()` had a channel-mapping bug: incoming red and blue pixel values were swapped before being passed to the classifier. The UCI Skin Segmentation dataset's column order is `B, G, R, y`; swapping red and blue inverts skin's characteristic R > G > B signature, which caused genuine skin pixels from real-world photographs to be misclassified. This was originally (incorrectly) attributed to a distribution mismatch between the training data's lab-photo sources and real-world conditions. This fix was identified and applied after the original 2024 submission, during later review of the project; once corrected, retesting on the same 2024 test images confirmed the model performs well in real-world conditions, consistent with its in-distribution metrics.

## Project structure

```
.
├── Analyze/              # Django project package (settings, root URLconf)
├── AprioriAPI/           # Market Basket Analysis app
│   ├── functions.py      # recommendation lookup + top-seller fallback
│   ├── models.py         # Item model (unmanaged, backed by an existing 'items' table)
│   ├── serializers.py
│   ├── converters.py     # custom float URL converter
│   ├── urls.py
│   └── views.py          # ItemViewSet (recommendations), AprioriView (re-fit rules)
├── KNNAPI/               # Skin Segmentation app
│   ├── urls.py
│   └── views.py          # KNNView (predict / re-fit classifier)
├── docs/                 # Static HTML/JS pages (Bootstrap + vanilla JS, fetch-based) — doubles as the
│   │                     # GitHub Pages source, see DEPLOY.md; also holds k_selection_plot.png below
│   ├── index.html        # landing page linking to both demos
│   ├── image.html        # skin-pixel classifier demo
│   ├── items.html        # related-products demo
│   └── k_selection_plot.png   # cross-validation accuracy plot, referenced from the README
├── manage.py
├── requirements.txt
├── items.sql             # seeds the unmanaged `items` table -- see Setup
└── rules.csv             # mined Apriori association rules -- see Association rules
```

## Setup

**Requires Python 3.12** (a `.python-version` file in the repo root pins this for tools that read it, e.g.
`pyenv`). Several dependencies here are pinned to 2024-era versions (`pandas==2.2.2`, `numpy==1.26.4`,
`scikit-learn==1.4.2`) with no pre-built wheel for newer Python releases — installing on, say, Python 3.14
falls back to compiling from source and fails outright (a C++ compilation error inside pandas' generated
code). This isn't specific to any one deployment platform; it'll happen in any environment on a too-new
interpreter.

This is the same codebase used both for running locally and for the deployed version — there's no separate
"deploy" copy. `Analyze/settings.py` reads `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `DATABASE_URL` from
environment variables, and falls back to sensible local defaults (including a local SQLite file) when
they're unset, so the steps below work with zero extra setup.

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run migrations (creates `db.sqlite3` locally, since no `DATABASE_URL` is set):
   ```
   python manage.py migrate
   ```
3. Load the `items` table — it's unmanaged (see `AprioriAPI/models.py`), so `migrate` doesn't create it:
   ```
   sqlite3 db.sqlite3 < items_postgres.sql
   ```
   (Despite the name, `items_postgres.sql` is plain ANSI SQL — no MySQL backticks or Postgres-only syntax —
   so it loads the same way into SQLite. If you'd rather run a real MySQL or Postgres server locally instead
   of SQLite, set `DATABASE_URL` accordingly — e.g. `mysql://user:pass@localhost:3306/Market` — and use
   `items.sql` or `items_postgres.sql` respectively.)
4. Start the development server:
   ```
   python manage.py runserver
   ```
5. Open `docs/index.html` in a browser — `docs/js/config.js` detects that it's being viewed locally
   (`file://` or `localhost`/`127.0.0.1`) and points the pages at `http://127.0.0.1:8000` automatically,
   matching step 4. No setting to check or reset — it stays this way regardless of what the same file is
   configured to use for the publicly hosted copy.

For hosting `docs/` publicly (e.g. GitHub Pages) so reviewers can try it with one click, see `DEPLOY.md`.

For deploying this same repo to Render, see `DEPLOY.md`.

## API reference

All endpoints below are throttled to 60 requests/minute per IP (`AnonRateThrottle` — there's no auth system,
so every caller is "anonymous"); exceeding it returns `429 Too Many Requests`. Mainly relevant for the public
deployment; irrelevant in practice for local/offline use.

### Apriori / Market Basket Analysis

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/apriori/items/` | List all items |
| `GET` | `/apriori/items/<name>/` | Up to 10 related items for `<name>`, drawn only from rules where `<name>` is a single-item antecedent (multi-item-antecedent rules aren't used here) — falls back to top sellers by quantity if fewer than 10 match |
| `POST` | `/apriori/metrics/<min_support>/<metric_name>/<metric_min_value>/` | Re-fit the Apriori model and association rules (`metric_name` is `lift` or `confidence`) |

Both views read and write under `AprioriAPI/static/AprioriAPI/CSVs/` — a hot-encoded basket matrix (`UK_Transactions.csv`) and a rules pickle (`pickles/association_rules2`, a subdirectory of `CSVs/`). Only `pickles/` is present in this repository; `UK_Transactions.csv` isn't. `items.sql` and `rules.csv` at the repo root are reproducibility/documentation artifacts built from the same methodology, not files these views read directly — regenerating `pickles/association_rules2` from the corrected `rules.csv` requires converting it back into a real pickle first (a plain CSV round-trip turns each rule's `frozenset` into a string, which silently breaks `get_related_items()`'s `len(list(x)) == 1` check), not just renaming the file. Re-fitting via `/apriori/metrics/.../` also only changes the support/metric threshold on the existing `UK_Transactions.csv` — it doesn't redo any cleaning, so it can't remove an item like `DOTCOM POSTAGE` from the universe; that requires regenerating `UK_Transactions.csv` itself via the pipeline in [Data preparation](#data-preparation).

Both views also originally used relative paths (e.g. `"AprioriAPI/static/AprioriAPI/CSVs/pickles/association_rules2"`) that only resolve correctly if Django happens to be launched from one specific working directory. `AprioriAPI/functions.py` and `AprioriAPI/views.py` now build these paths from `settings.BASE_DIR` instead, so they work regardless of the working directory the server is started from.

### k-NN / Skin Segmentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/knn/image/<R>/<G>/<B>/` | Predict skin (`1`) / non-skin (`2`) for the given pixel |
| `POST` | `/knn/parameter/<k>/` | Re-fit the k-NN classifier with the given `k` and persist it |

## Datasets

**Market Basket Analysis**: Chen, D. (2015). [Online Retail](https://doi.org/10.24432/C5BW33) [Dataset]. UCI Machine Learning Repository. Licensed under CC BY 4.0. Obtained via a re-hosted copy on [Kaggle — Market Basket Analysis](https://www.kaggle.com/datasets/aslanahmedov/market-basket-analysis) (UK online retail transaction history). The raw export itself isn't included in this repository, but the derived `items` table is — see [Data preparation](#data-preparation) and `items.sql`.

**Skin Segmentation**: Bhatt, R. & Dhall, A. (2009). *Skin Segmentation* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5T30C. Licensed under CC BY 4.0. 245,057 pixel samples (50,859 skin, 194,198 non-skin) drawn from the Color FERET and PAL face databases across a range of ages, ethnicities, and genders. Included in this repository as `dataset.csv` — it's read at request time by `KNNAPI` to fit the scaler, so it's required for the API to function, not just background reference material.

## k-NN model selection

`k=5` (used by `KNNAPI`) wasn't chosen arbitrarily. This section documents how it was selected and the final model evaluated. The code below is transcribed verbatim from the original coursework analysis — not included in this repository — and independently verified by rerunning it against `dataset.csv`; it was never part of the Django app itself, since it was a one-off analysis run ahead of hardcoding the result.

**Selecting `k` via 5-fold cross-validation:**

```python
X = data.drop('y', axis=1)
y = data['y']

k_values = [i for i in range(1,31)]
scores = []

scaler = StandardScaler()
X = scaler.fit_transform(X)

for k in k_values:
    knn = KNeighborsClassifier(n_neighbors=k, weights='distance')
    score = cross_val_score(knn, X, y, cv=5)
    scores.append(np.mean(score))
```

**Plotting accuracy against `k`:**

```python
sns.lineplot(x = k_values, y = scores, marker = 'o')
plt.xlabel("K Values")
plt.ylabel("Accuracy Score")
plt.show()
```

![Cross-validation accuracy against k](docs/k_selection_plot.png)

Every value of `k` scores above 98.9%, and `k=5` gives the highest mean cross-validation accuracy — **≈99.22%** — confirmed by rerunning the code above directly against the dataset.

**Training the final model — and a real bug found in it:**

```python
best_index = np.argmax(scores)
best_k = k_values[best_index]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y.values.ravel(), test_size=0.2)

knn = KNeighborsClassifier(n_neighbors=best_index, weights='distance')
knn.fit(X_train, y_train)

# Save the model
jl.dump(knn, 'KNN4.pkl')

y_pred = knn.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average=None)
recall = recall_score(y_test, y_pred, average=None)

print("Accuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
```
```
Accuracy: 0.9998775810005713
Precision: [0.99950961 0.99997424]
Recall: [0.99990188 0.9998712 ]
```

`best_k = k_values[best_index]` is correct — it maps the 0-based position of the top score back to the actual k value (`k_values = range(1, 31)`, so `k_values[i] = i + 1`), giving `best_k = 5`. The bug is on the next block: `best_k` is computed and then never used. `KNeighborsClassifier(n_neighbors=best_index, ...)` passes the raw array index instead, so the model that was actually fit and pickled as `KNN4.pkl` used **`n_neighbors=4`** (`best_index`), not the cross-validation-selected `best_k=5`.

Verified impact: rerunning both versions on an identical held-out split gave 99.949% accuracy at `n_neighbors=4` (buggy) versus 99.943% at `n_neighbors=5` (fixed) — a ~0.006-point difference. The bug is real and worth fixing (change `n_neighbors=best_index` to `n_neighbors=best_k` before retraining), but it didn't produce a materially different model; both k values perform almost identically on this dataset.


## Data preparation

Neither the raw Kaggle export nor a cleaned copy of it is included in this repository — the Kaggle dataset is licensed "Data files © Original Authors" (see [Datasets](#datasets)), which doesn't grant redistribution rights at the row level, even after cleaning. What's included instead is the code below, `items.sql`, and `rules.csv`: anyone who obtains their own copy of the raw export can reproduce everything from here.

**1. Clean the raw export:**

```python
import pandas as pd

data = pd.read_csv("Assignment-1_Data.csv", sep=';', encoding='utf-8-sig')

# Strip runs of 2+ spaces entirely (not to a single space -- this does mean
# some names lose a word boundary, e.g. "BALLOONS  WRITING SET" becomes
# "BALLOONSWRITING SET". That's the actual behaviour of the original 2024
# code and is reproduced faithfully here rather than silently corrected.)
data['Itemname'] = data['Itemname'].str.replace(r'\s{2,}', '', regex=True)

# Trim stray characters
data['Itemname'] = data['Itemname'].str.replace(r'\.', '', regex=True)
data['Itemname'] = data['Itemname'].str.replace(r'\*', '', regex=True)
data['Price'] = data['Price'].str.replace(',', '.')

# Drop rows with no invoice number
data.dropna(subset=['BillNo'], inplace=True)
data['BillNo'] = data['BillNo'].astype('str')

# Drop cancelled invoices (BillNo containing 'C')
data = data[~data['BillNo'].str.contains('C')]

# Drop rows with non-positive price or quantity
data = data[(data['Price'].astype('float') > 0) & (data['Quantity'].astype('int') > 0)]

# Drop rows with no item name
data = data[~data['Itemname'].isna()]
```

**2. Build the `items` reference table:**

```python
ADMIN_EXCLUDE = {
    'AMAZON FEE', 'Adjust bad debt', 'Bank Charges', 'CARRIAGE', 'DOTCOM POSTAGE',
    'Manual', 'Next Day Carriage', 'POSTAGE', 'SAMPLES',
    'Dotcomgiftshop Gift Voucher £1000', 'Dotcomgiftshop Gift Voucher £2000',
    'Dotcomgiftshop Gift Voucher £3000', 'Dotcomgiftshop Gift Voucher £4000',
    'Dotcomgiftshop Gift Voucher £5000', 'Dotcomgiftshop Gift Voucher £10000',
}  # shipping/fee/voucher line items, not products -- survive step 1's price/quantity

uk = data[data['Country'] == 'United Kingdom'].copy()
uk = uk[~uk['Itemname'].isin(ADMIN_EXCLUDE)]
uk['Price'] = uk['Price'].astype(float)

items = uk.groupby('Itemname').agg(
    quantity=('Quantity', 'sum'),
    price=('Price', lambda x: x.mode().iloc[0]),   # see note below -- NOT mean or weighted average
).reset_index()
```

The `price` for each item is the **mode** (most frequently occurring price for that item), not a mean or quantity-weighted average. This was verified directly against the live app's displayed prices for six known items (e.g. `WHITE HANGING HEART T-LIGHT HOLDER` at £2.95, `REGENCY CAKESTAND 3 TIER` at £12.75) — mode matched exactly in every case; weighted average, plain mean, and most-recent-price all did not. An earlier version of this documentation stated a quantity-weighted-average formula; that was incorrect and has been corrected here.

This produces **3,981 items** from the cleaned UK data — see `items.sql` for the ready-to-load result (schema is a reasonable reconstruction; the actual Django migration for `Item` wasn't available when this was generated, so adjust column types if yours differ).

## Association rules

**3. Build the UK invoice basket and mine association rules:**

```python
from mlxtend.frequent_patterns import apriori, association_rules

uk_baskets = data[data['Country'] == 'United Kingdom'].copy()
uk_baskets = uk_baskets[~uk_baskets['Itemname'].isin(ADMIN_EXCLUDE)]

basket_UK = (uk_baskets.groupby(['BillNo', 'Itemname'])['Quantity']
             .sum().unstack().fillna(0))

def hot_encode(x):
    if x <= 0:
        return 0
    if x >= 1:
        return 1

basket_UK = basket_UK.map(hot_encode)

frq_items = apriori(basket_UK, min_support=0.01, use_colnames=True, low_memory=True)
rules = association_rules(frq_items, metric="lift", min_threshold=1)
rules = rules.sort_values(['confidence', 'lift'], ascending=[False, False])
rules.to_csv("rules.csv")
```

This is the same mining code and parameters as the original 2024 pipeline (`min_support=0.01`, `metric="lift"`, `min_threshold=1`), with one change: `ADMIN_EXCLUDE` — `POSTAGE`, `DOTCOM POSTAGE`, `CARRIAGE`, `Next Day Carriage`, `Manual`, `SAMPLES`, `Bank Charges`, `AMAZON FEE`, `Adjust bad debt`, and six `Dotcomgiftshop Gift Voucher` denominations, the same 15 non-product entries excluded from `items.sql` above — is removed from the basket **before** it's built, rather than filtered out of the results afterwards. In 2024, `DOTCOM POSTAGE` — a shipping charge, not a product — was left in and ended up in 492 of the resulting rules. Excluding all 15 up front instead gives **3,992 rules**, none of which involve any of them.

Removing an item as a post-hoc filter instead of rebuilding the basket isn't quite equivalent: doing it properly this way changes which itemsets clear the 1% support threshold at all (not just the ones directly involving the excluded items), since removing invoices that were previously counted in the basket shifts the denominator every support figure is computed against. `confidence` is unaffected either way — it's a ratio of basket counts internal to each rule and doesn't depend on the total basket count.



## Known limitations

- `CORS_ALLOWED_ORIGINS` defaults to `['null']` (configurable via env var — see `DEPLOY.md`), which only permits requests from `file://` origins — sufficient for opening the static frontend pages directly, but will need setting explicitly for any other deployment.
- The `StandardScaler` used for k-NN prediction is refit on the full dataset on every request rather than persisted alongside the trained model.
- Both `POST /knn/parameter/<k>/` and `AprioriView`'s re-fit endpoint (`POST /apriori/metrics/.../`) write a
  single shared model/rules file on disk with no per-user or per-session isolation — fine for one local
  user, but in a deployment with multiple simultaneous visitors, one visitor's chosen parameters would
  silently change what every other visitor sees next. `AprioriView`'s endpoint additionally reads
  `UK_Transactions.csv` — the hot-encoded UK invoice basket matrix — which isn't included in this
  repository. Unlike `items.sql` and `rules.csv`, this file preserves every invoice at full original
  resolution (one row per real transaction, no aggregation), which sits closer to redistributing the
  licensed dataset itself than to a genuinely transformed derivative, so it isn't published here; the code
  to regenerate it from a legitimately-obtained copy of the raw export is in
  [Association rules](#association-rules).
- Because of the above, both endpoints are gated behind `KNN_TUNING_ENABLED` / `APRIORI_TUNING_ENABLED`
  settings (env vars, default `True`) and return a `503` with an explanation when turned off, rather than
  behaving incorrectly or crashing. They're switched off on the public deployment and work normally for
  local/offline use — see `DEPLOY.md`.

## References

1. Chen, D. (2015). [Online Retail](https://doi.org/10.24432/C5BW33) [Dataset]. UCI Machine Learning Repository. CC BY 4.0. Obtained via [Kaggle — Market Basket Analysis](https://www.kaggle.com/datasets/aslanahmedov/market-basket-analysis).
2. [Implementing Apriori algorithm in Python](https://www.geeksforgeeks.org/machine-learning/implementing-apriori-algorithm-in-python/) — GeeksforGeeks
3. [How to build and implement a recommendation system from scratch (in Python)](https://ubiops.com/how-to-build-and-implement-a-recommendation-system-from-scratch-in-python/) — UbiOps
4. [K-Nearest Neighbors (KNN) Classification with scikit-learn](https://www.datacamp.com/tutorial/k-nearest-neighbor-classification-scikit-learn) — DataCamp
5. Bhatt, R. & Dhall, A. (2009). [Skin Segmentation](https://doi.org/10.24432/C5T30C) [Dataset]. UCI Machine Learning Repository. CC BY 4.0.

## License

MIT — see [LICENSE](LICENSE).