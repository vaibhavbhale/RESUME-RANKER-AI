from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("rank/", views.upload_and_rank, name="upload"),
    path("batches/<int:batch_id>/", views.results, name="results"),
    path("results/<int:result_id>/", views.result_detail, name="result_detail"),
]
