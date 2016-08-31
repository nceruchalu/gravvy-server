from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from imagekit.admin import AdminThumbnail

from gravvy.apps.account.models import User, AuthToken, RegistrationProfile
from gravvy.apps.account.forms import UserChangeForm, UserCreationForm

# Register your models here.

class MyUserAdmin(UserAdmin):
    """
    Custom version of the ModelAdmin associated with the User model. It is 
    modified to work with the custom User model
    """
    # use the custom "delete selected objects" action
    actions = ['delete_selected_u']
    
    # These fields to be used in displaying the User model. These override the
    # definitions on the base UserAdmin that reference specific fields on
    # auth.User
    list_display =  ('phone_number', 'full_name', 'date_joined', 'is_staff',)
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'avatar', 
                                         'avatar_thumbnail')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 
                                           'updated_at')}),
        )
    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields': ('phone_number', 'password1', 'password2'),
                }),
        )
    search_fields = ('phone_number', 'full_name')
    ordering = ('-date_joined',)
    
    readonly_fields = ('avatar_thumbnail', 'last_login', 'date_joined', 
                       'updated_at', )
    avatar_thumbnail = AdminThumbnail(image_field='avatar_thumbnail')
        
    # changing the displayed fields via `fieldsets` requires updating the form
    form = UserChangeForm
    # customizing the User model requires changing the add form
    add_form = UserCreationForm
    
    def get_actions(self, request):
        """
        Permanently disable the default "deleted selected objects" action for 
        this ModelAdmin
          
        Args:   
            request: HttpRequest object representing current request
            
        Returns:
            Updated list of actions.
        """
        actions = super(MyUserAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def delete_selected_u(self, request, queryset):
        """
        Version of the "deleted selected objects" action which calls the model's
        `delete()` method. This is needed because the default version uses 
        `QuerySet.delete()`, which doesn't call the model's `delete()` method.
        
        Args:
            request: HttpRequest object representing current request
            queryset: QuerySet of set of User objects selected by admin
        """
        for obj in queryset:
            obj.delete()
    delete_selected_u.short_description = "Delete selected user(s)"


class AuthTokenAdmin(admin.ModelAdmin):
    """
    Representation of the AuthToken model in the admin interface.
    """
    list_display = ('key', 'user', 'created_at', 'updated_at')
    fields = ('user', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def has_add_permission(self, request): 
        """
        Don't want users adding Auth Tokens through admin 
          
        Args:   
            request: HttpRequest object representing current request
            
        Returns:      
            (Boolean) False
        """
        return False
    

class RegistrationAdmin(admin.ModelAdmin):
    """
    Representation of the RegistrationProfile model in the admin interface.
    """
    # use the custom "delete sected objects" action
    actions = ['activate_users', 'resend_verification_sms']
    list_display = ('user', 'verification_code_expired')
    fields = ('user', 'verification_code', 'created_at', 'updated_at')
    readonly_fields = ('user', 'verification_code', 'created_at', 'updated_at')
    raw_id_fields = ['user']
    search_fields = ('user__phone_number', 'user__full_name',)

    def activate_users(self, request, queryset):
        """
        Activates the selected users, if they are not already activated.
        
        Args:
            request: HttpRequest object representing current request
            queryset: QuerySet of RegistrationProfile objects selected by admin
        """
        for profile in queryset:
            RegistrationProfile.objects.activate_user(
                profile.user, profile.verification_code)
    activate_users.short_description = _("Activate users")

    def resend_verification_sms(self, request, queryset):
        """
        Re-sends verfication code SMS messages for the selected users.

        Note that this will *only* send verification sms for users who are
        eligible to activate:
            * SMS messages will not be sent to users whose verification codes 
              have expired or who have already expired.
            * SMS messages will not be sent to users who are already active.
        
        Args:
            request: HttpRequest object representing current request        
        """
        for profile in queryset:
            if not profile.verification_code_expired():
                profile.send_verification_sms()
    resend_verification_sms.short_description = _("Re-send verification codes")


# Register UserAdmin
admin.site.register(User, MyUserAdmin)
# Register AuthTokenAdmin
admin.site.register(AuthToken, AuthTokenAdmin)
# Register RegistrationAdmin
admin.site.register(RegistrationProfile, RegistrationAdmin)




