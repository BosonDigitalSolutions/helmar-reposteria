from django.urls import path

from .views import ProductionCalendarView, ProductionDayView, ProductionJobUpdateView

app_name = "production"

urlpatterns = [
    path("", ProductionCalendarView.as_view(), name="calendar"),
    path("dia/<str:day>/", ProductionDayView.as_view(), name="day"),
    path("ficha/<int:pk>/", ProductionJobUpdateView.as_view(), name="job_detail"),
]
