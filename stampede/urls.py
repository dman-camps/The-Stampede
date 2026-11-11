from django.urls import include, path
from allauth.account import views as account_views
from stamps import views, home_views

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('', home_views.home, name='home'),
    path('search/', home_views.search, name='search'),
    path('profile/', views.profile, name='profile'),
    path('users/<str:username>/', views.profile, name='public_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/confirm/', views.confirm_profile, name='confirm_profile'),
    path('users/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),
    path('create/', views.create, name='create'),
    path('register/', account_views.SignupView.as_view(), name='register'),
    path('login/', account_views.LoginView.as_view(), name='login'),
    path('logout/', account_views.LogoutView.as_view(), name='logout'),
    path('verify/', account_views.email_verification_sent, name='verify_email'),
    path('stamps/<int:pk>/', views.stamp_detail, name='stamp_detail'),
    path('stamps/<int:pk>/join/', views.join_permission, name='join_permission'),
    path('stamps/<int:pk>/participants/', views.stamp_participants, name='stamp_participants'),
    path('stamps/<int:pk>/leave/', views.leave_stamp, name='leave_stamp'),
    path('stamps/<int:pk>/edit/', views.edit_stamp, name='edit_stamp'),
    path('stamps/<int:pk>/cancel/', views.cancel_stamp, name='cancel_stamp'),
    path('stamps/<int:pk>/delete/', views.delete_stamp, name='delete_stamp'),
    path('stamps/<int:pk>/report/', views.report_stamp, name='report_stamp'),
    path("account/", views.account, name="account"),
]
