from django.contrib import admin

from .models import Quote, QuoteLine, QuoteRevision


class QuoteLineInline(admin.TabularInline):
    model = QuoteLine
    extra = 0


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("folio", "contact", "status", "version", "event_date", "total")
    list_filter = ("status",)
    search_fields = ("folio", "contact__first_name", "contact__last_name")
    inlines = [QuoteLineInline]


@admin.register(QuoteRevision)
class QuoteRevisionAdmin(admin.ModelAdmin):
    list_display = ("quote", "number", "sent_at")
