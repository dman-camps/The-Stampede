from django.contrib import admin
from .models import Report, Stamp, StampParticipation, UserFollow, UserProfile


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('stamp', 'reporter', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('stamp__title', 'reporter__username', 'reason')
    readonly_fields = ('reporter', 'stamp', 'reason', 'created_at')
    actions = ('mark_reviewed', 'dismiss_reports')

    @admin.action(description='Mark selected reports as reviewed')
    def mark_reviewed(self, request, queryset):
        queryset.update(status='reviewed')

    @admin.action(description='Dismiss selected reports')
    def dismiss_reports(self, request, queryset):
        queryset.update(status='dismissed')


@admin.register(Stamp)
class StampAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'date', 'location', 'is_cancelled')
    list_filter = ('category', 'is_cancelled', 'date')
    search_fields = ('title', 'desc', 'location', 'creator__username')


admin.site.register(StampParticipation)
admin.site.register(UserProfile)
admin.site.register(UserFollow)
