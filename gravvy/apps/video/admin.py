from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from imagekit.admin import AdminThumbnail

from gravvy.apps.video.models import Video, VideoUsers, Clip

# Register your models here.

class ClipInline(admin.TabularInline):
    """
    Representation of a Clip to be used inline in the VideoAdmin
    """
    model = Clip
    fields = ('mp4', 'photo', 'owner', 'order',)
    readonly_fields = ('mp4', 'photo', 'owner', 'order',)


class VideoAdmin(admin.ModelAdmin):
    """
    Representation of a Video in the admin interface
    """
    # use the custom "delete selected objects" action
    actions = ['delete_selected_v']
    
    list_display = ('hash_key', 'owner', 'title', 'likes_count', 'plays_count',
                    'score', 'created_at')
    
    fieldsets = (
        (None, {'fields': ('hash_key', 'title', 'owner')}),
        (_('Details'), {'fields': ('description','likes_count','plays_count',
                                   'score')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
        (_('Leading Clip Media'), {'fields': ('photo', 'photo_thumbnail', 
                                              'photo_small_thumbnail',)}),
        (_('Clips'), {'fields': ('clips_count', 'duration',)}),
        (_('Users'), {'fields': ('users',)}),
        )
    readonly_fields = ('hash_key', 'likes_count', 'plays_count', 'score',
                       'updated_at', 'created_at', 
                       'photo', 'photo_thumbnail', 'photo_small_thumbnail',
                       'clips_count', 'duration', 'users',)
    inlines = (ClipInline,)
    search_fields = ('title', 'owner__phone_number', 'owner__full_name')
    ordering = ('-created_at',)
    
    photo_thumbnail = AdminThumbnail(image_field='photo_thumbnail')
    photo_small_thumbnail = AdminThumbnail(image_field='photo_small_thumbnail')
    
    def get_actions(self, request):
        """
        Permanently disable the default "deleted selected objects" action for 
        this ModelAdmin
          
        Args:   
            request: HttpRequest object representing current request
            
        Returns:
            Updated list of actions.
        """
        actions = super(VideoAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    
    def delete_selected_v(self, request, queryset):
        """
        Version of the "deleted selected objects" action which calls the model's
        `delete()` method. This is needed because the default version uses 
        `QuerySet.delete()`, which doesn't call the model's `delete()` method.
        
        Args:
            request: HttpRequest object representing current request
            queryset: QuerySet of set of Video objects selected by admin
        """
        for obj in queryset:
            obj.delete()
    delete_selected_v.short_description = "Delete selected video(s)"


class VideoUsersAdmin(admin.ModelAdmin):
    """
    Representation of a VideoUser in the admin interface
    """ 
    list_display = ('video', 'user', 'hash_key', 'new_likes_count', 
                    'new_clips_count', 'status')
    fieldsets = (
        (None, {'fields': ('video', 'user', 'hash_key')}),
        (_('Status'), {'fields': ('status','new_likes_count',
                                  'new_clips_count')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
        )
    readonly_fields = ('hash_key', 'created_at', 'updated_at')
    search_fields = ('video__title', 'video__hash_key' 'owner__phone_number', 
                     'owner__full_name')
    

class ClipAdmin(admin.ModelAdmin):
    """
    Representation of a Clip in the admin interface
    """
    # use the custom "delete selected objects" action
    actions = ['delete_selected_c']
    
    list_display = ('id', 'video', 'owner', 'order')
    fieldsets = (
        (None, {'fields': ('video', 'owner', 'order')}),
        (_('Media'), {'fields': ('mp4', 'photo', 'photo_thumbnail',
                                 'duration')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
        )
    readonly_fields = ('order', 'photo_thumbnail', 'created_at', 'updated_at',)
    search_fields = ('video__title', 'video__hash_key' 'owner__phone_number', 
                     'owner__full_name')
    ordering = ('-video__created_at', '-order',)
    
    photo_thumbnail = AdminThumbnail(image_field='photo_thumbnail')
    
    def get_actions(self, request):
        """
        Permanently disable the default "deleted selected objects" action for 
        this ModelAdmin
          
        Args:   
            request: HttpRequest object representing current request
            
        Returns:
            Updated list of actions.
        """
        actions = super(ClipAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def delete_selected_c(self, request, queryset):
        """
        Version of the "deleted selected objects" action which calls the model's
        `delete()` method. This is needed because the default version uses 
        `QuerySet.delete()`, which doesn't call the model's `delete()` method.
        
        Args:
            request: HttpRequest object representing current request
            queryset: QuerySet of set of Clip objects selected by admin
        """
        for obj in queryset:
            obj.delete()
    delete_selected_c.short_description = "Delete selected clip(s)"


admin.site.register(Video, VideoAdmin)
admin.site.register(VideoUsers, VideoUsersAdmin)
admin.site.register(Clip, ClipAdmin)
