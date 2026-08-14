from .auth import logout_view, register, join, dismiss_tutorial, CustomPasswordChangeView
from .home import home
from .profile import (
    profile, profile_edit, avatar_upload, email_change, email_change_confirm,
    delete_account, export_data, notification_preferences,
    github_connect, github_disconnect, notification_read, notification_list,
)
from .pomodoro import pomodoro, pomodoro_save
from .push import push_status, service_worker
