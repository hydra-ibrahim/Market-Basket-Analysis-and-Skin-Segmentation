from django.urls import path, register_converter

from . import views, converters

register_converter(converters.FloatUrlParameterConverter, 'float')

urlpatterns = [
    path('items/', views.ItemViewSet.as_view({'get':'list'}), name='items'),
    path('items/<str:name>/', views.ItemViewSet.as_view({'get':'retrieve'}), name='item'),

    path('metrics/<float:min_support>/<str:metric_name>/<float:metric_min_value>/', 
            views.AprioriView.as_view(), name='metrics'),
    
    # path('items/', views.ItemsList.as_view(), 'items'),
    # path('items/<str:item>/', views.ItemView, 'item')
]
