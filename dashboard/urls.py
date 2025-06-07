from django.urls import path
from . import views

urlpatterns = [
    path('', views.fetch_data, name='fetch_data'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('domain/<int:domain_id>/extensions/', views.domain_extensions, name='domain_extensions'),
    path('domain/<int:domain_id>/filter/<str:file_type>/', views.filter_urls, name='filter_urls'),
    path('domain/<int:domain_id>/delete/', views.delete_domain, name='delete_domain'),
    path("manage-filters/", views.manage_filters, name="manage_filters"),
    path("about/", views.about, name="about"),

#     path('filter/<int:domain_id>/<str:file_type>/', views.filter_urls, name='filter_urls'),
]