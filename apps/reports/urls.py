from django.urls import path

from .views import ResultView

app_name = "reports"

urlpatterns = [
    path("", ResultView.as_view(), name="result"),
]
