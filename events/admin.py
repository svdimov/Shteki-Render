from django.contrib import admin

from events.models import Event, EventPost, EventLike


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass

@admin.register(EventPost)
class EventPostAdmin(admin.ModelAdmin):
   pass

# @admin.register(EventLike)
# class EventLikeAdmin(admin.ModelAdmin):
#     pass