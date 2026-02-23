from django.contrib import admin
from django.contrib import admin

from common.models import EventParticipation




@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', )
    list_filter = ('status',)
    search_fields = ('user__email', 'event__name',)
    ordering = ('-created_at',)



