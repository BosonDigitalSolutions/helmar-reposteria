from django.urls import path

from .views import (
    QuoteAcceptView,
    QuoteCreateView,
    QuoteDetailView,
    QuoteExpireView,
    QuoteListView,
    QuoteRejectView,
    QuoteSendView,
    QuoteUpdateView,
)

app_name = "quotations"

urlpatterns = [
    path("", QuoteListView.as_view(), name="quote_list"),
    path("nueva/", QuoteCreateView.as_view(), name="quote_create"),
    path("<int:pk>/", QuoteDetailView.as_view(), name="quote_detail"),
    path("<int:pk>/editar/", QuoteUpdateView.as_view(), name="quote_update"),
    path("<int:pk>/enviar/", QuoteSendView.as_view(), name="quote_send"),
    path("<int:pk>/aceptar/", QuoteAcceptView.as_view(), name="quote_accept"),
    path("<int:pk>/rechazar/", QuoteRejectView.as_view(), name="quote_reject"),
    path("<int:pk>/vencer/", QuoteExpireView.as_view(), name="quote_expire"),
]
