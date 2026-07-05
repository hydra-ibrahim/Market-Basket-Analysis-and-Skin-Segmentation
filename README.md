# Market Basket Analysis and Skin Segmentation

A Django REST API combining two independent machine learning pipelines: an Apriori-based product recommendation engine for a mock e-commerce inventory, and a k-Nearest Neighbours skin-pixel classifier served through a browser canvas interface.

Built as my course project (Information Systems Engineering) in Informatics Engineering at Tishreen University, 2024. All design, implementation, and analysis in this repository is my own work.

## Contents

- [Overview](#overview)
- [Project structure](#project-structure)
- [Setup](#setup)
- [API reference](#api-reference)
- [Datasets](#datasets)
- [Data preparation](#data-preparation)
- [Known limitations](#known-limitations)
- [References](#references)
- [License](#license)

## Overview

Two independent Django apps sit behind a single REST API.

**`AprioriAPI`** mines association rules from a UK online-retail transaction history using the Apriori algorithm (via `mlxtend`), then serves up to ten related-item recommendations for a given product. If fewer than ten rule-based matches exist for an item, the recommendation list is topped up with the store's best-selling items.

**`KNNAPI`** classifies a single R/G/B pixel as skin or non-skin using a k-Nearest Neighbours classifier (`scikit-learn`), trained on the UCI Skin Segmentation dataset. A canvas-based frontend page lets a user click a pixel on an uploaded image and get a live prediction.

Both apps also expose a parameter-adjustment endpoint that re-fits the underlying model (Apriori support/metric thresholds, or `k` for the classifier) and persists the result to disk.

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
├── Frontend/             # Static HTML/JS pages (Bootstrap + vanilla JS, fetch-based)
├── manage.py
└── requirements.txt
```

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Create a MySQL database matching `Analyze/settings.py`, and set `SECRET_KEY` and the database credentials via environment variables rather than the placeholder values in the settings file.
3. Run migrations and start the development server:
   ```
   python manage.py migrate
   python manage.py runserver
   ```
4. Open any page under `Frontend/` in a browser — the pages call the API directly at `http://127.0.0.1:8000`.

## API reference

### Apriori / Market Basket Analysis

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/apriori/items/` | List all items |
| `GET` | `/apriori/items/<name>/` | Up to 10 related items for `<name>`, falling back to top sellers if fewer than 10 association rules match |
| `POST` | `/apriori/metrics/<min_support>/<metric_name>/<metric_min_value>/` | Re-fit the Apriori model and association rules (`metric_name` is `lift` or `confidence`) |

### k-NN / Skin Segmentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/knn/image/<R>/<G>/<B>/` | Predict skin (`1`) / non-skin (`2`) for the given pixel |
| `POST` | `/knn/parameter/<k>/` | Re-fit the k-NN classifier with the given `k` and persist it |

## Datasets

**Market Basket Analysis**: [Kaggle — Market Basket Analysis](https://www.kaggle.com/datasets/aslanahmedov/market-basket-analysis) (UK online retail transaction history). Not included in this repository — the raw export is cleaned and filtered to UK-only transactions before being consumed by `AprioriAPI`.

**Skin Segmentation**: Bhatt, R. & Dhall, A. (2009). *Skin Segmentation* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5T30C. Licensed under CC BY 4.0. 245,057 pixel samples (50,859 skin, 194,198 non-skin) drawn from the Color FERET and PAL face databases across a range of ages, ethnicities, and genders. Included in this repository as `dataset.csv` — it's read at request time by `KNNAPI` to fit the scaler, so it's required for the API to function, not just background reference material.

## Data preparation

The `items` table consumed by `AprioriAPI.models.Item` (`name`, `quantity`, `price`) is not a direct dump of the Kaggle export — it's built from it in pandas:

1. Group the raw transaction rows by unique `Itemname`.
2. Sum `Quantity` across all of an item's transaction rows to get its total quantity.
3. Derive a single representative `price` per item as a quantity-weighted average — `sum(Quantity × Price) / sum(Quantity)` across that item's rows — rather than a plain mean, so that high-volume transactions influence the item's price more than one-off outlier rows.
4. Load the resulting `(name, quantity, price)` rows into the `items` SQL table.

Some additional cleaning of item names, prices, and quantities was applied to the raw export before this aggregation; the exact set of steps hasn't been fully re-documented here.

## Known limitations

- The k-NN classifier performs very well on the Skin Segmentation benchmark itself but generalises poorly to arbitrary uploaded photos. The most likely cause is a distribution mismatch: the training pixels come from controlled lab photography (FERET/PAL), not the lighting and camera conditions of typical everyday images.
- `CORS_ALLOWED_ORIGINS` is set to `['null']`, which only permits requests from `file://` origins — sufficient for opening the static frontend pages directly, but will need updating for any other deployment.
- The `StandardScaler` used for k-NN prediction is refit on the full dataset on every request rather than persisted alongside the trained model.

## References

1. [Market Basket Analysis Dataset](https://www.kaggle.com/datasets/aslanahmedov/market-basket-analysis) — Kaggle
2. [Implementing Apriori algorithm in Python](https://www.geeksforgeeks.org/machine-learning/implementing-apriori-algorithm-in-python/) — GeeksforGeeks
3. How to build and implement a recommendation system from scratch (in Python)
4. [K-Nearest Neighbors (KNN) Classification with scikit-learn](https://www.datacamp.com/tutorial/k-nearest-neighbor-classification-scikit-learn) — DataCamp
5. Bhatt, R. & Dhall, A. (2009). [Skin Segmentation](https://doi.org/10.24432/C5T30C) [Dataset]. UCI Machine Learning Repository. CC BY 4.0.

## License

MIT — see [LICENSE](LICENSE).