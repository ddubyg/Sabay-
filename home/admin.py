from django.contrib import admin
from .models import Activity, Participation


class ParticipationInline(admin.TabularInline):
    model = Participation
    extra = 0


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'creator', 'starts_at', 'created_at')
    list_filter = ('category',)
    inlines = [ParticipationInline]


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'joined_at')
