from django.urls import path

from .views import (
    ActivityCreateView,
    ContactCreateView,
    ContactDeleteView,
    ContactDetailView,
    ContactListView,
    ContactUpdateView,
    CrmSettingsUpdateView,
    ImportConfirmView,
    ImportPreviewView,
    ImportUploadView,
    NoteCreateView,
    OpportunityBoardView,
    OpportunityCreateView,
    OpportunityMoveView,
)

app_name = "crm"

urlpatterns = [
    path("", ContactListView.as_view(), name="contact_list"),
    path("nuevo/", ContactCreateView.as_view(), name="contact_create"),
    path("importar/", ImportUploadView.as_view(), name="import_upload"),
    path("importar/<int:pk>/", ImportPreviewView.as_view(), name="import_preview"),
    path("importar/<int:pk>/confirmar/", ImportConfirmView.as_view(), name="import_confirm"),
    path("reglas/", CrmSettingsUpdateView.as_view(), name="settings"),
    path("oportunidades/", OpportunityBoardView.as_view(), name="opportunity_board"),
    path("oportunidades/nueva/", OpportunityCreateView.as_view(), name="opportunity_create"),
    path("oportunidades/<int:pk>/mover/", OpportunityMoveView.as_view(), name="opportunity_move"),
    path("<int:pk>/", ContactDetailView.as_view(), name="contact_detail"),
    path("<int:pk>/editar/", ContactUpdateView.as_view(), name="contact_update"),
    path("<int:pk>/eliminar/", ContactDeleteView.as_view(), name="contact_delete"),
    path("<int:pk>/notas/", NoteCreateView.as_view(), name="note_create"),
    path("<int:pk>/actividades/", ActivityCreateView.as_view(), name="activity_create"),
]
