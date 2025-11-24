from django.urls import path
from . import views

urlpatterns = [
    path('train/', views.train_api, name='train'),
    path('predict/', views.predict_api, name='predict'),
    path('insights/trend/', views.trend_api, name='trend'),
    path('insights/funnel/', views.funnel_api, name='funnel'),
    path('insights/feature_importance/', views.feature_importance_api, name='feature_importance'),
    path('report/generate/', views.generate_report_api, name='generate_report'),
    path('chatbot/query/', views.chatbot_query_api, name='chatbot_query'),
]
