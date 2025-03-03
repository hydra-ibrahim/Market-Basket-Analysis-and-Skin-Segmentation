from django.urls import path
from .views import KNNView

urlpatterns = [
    path("image/<int:R>/<int:G>/<int:B>/", KNNView.as_view(), name="image"),
    path("parameter/<int:k>/", KNNView.as_view(), name="parameter"),
]
