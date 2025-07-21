from django.contrib import admin
from django.contrib.admin.models import LogEntry

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ['action_time', 'user', 'content_type', 'object_repr']
    search_fields = ['user__username', 'object_repr']

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False