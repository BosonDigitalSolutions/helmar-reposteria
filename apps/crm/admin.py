from django.contrib import admin

from .models import (
    Activity,
    Contact,
    ContactStatusLog,
    CrmSettings,
    Note,
    Opportunity,
    OpportunityStageLog,
    Tag,
)


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0


class OpportunityInline(admin.TabularInline):
    model = Opportunity
    extra = 0


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "status", "origin", "owner")
    list_filter = ("status", "origin")
    search_fields = ("first_name", "last_name", "email", "phone", "company")
    inlines = [NoteInline, OpportunityInline]


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("title", "contact", "stage", "owner", "updated_at")
    list_filter = ("stage",)


admin.site.register(Tag)
admin.site.register(CrmSettings)
admin.site.register(Activity)
admin.site.register(ContactStatusLog)
admin.site.register(OpportunityStageLog)
