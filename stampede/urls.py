from django.urls import include, path
from allauth.account import views as account_views
from stamps import views, home_views

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('', home_views.home, name='home'),
    path('create/', views.create, name='create'),
    path('register/', account_views.SignupView.as_view(), name='register'),
    path('login/', account_views.LoginView.as_view(), name='login'),
    path('logout/', account_views.LogoutView.as_view(), name='logout'),
    path('verify/', account_views.email_verification_sent, name='verify_email'),
    path('stamps/<int:pk>/', views.stamp_detail, name='stamp_detail'),
    path('stamps/<int:pk>/join/', views.join_permission, name='join_permission'),
    path('stamps/<int:pk>/participants/', views.stamp_participants, name='stamp_participants'),
    path('stamps/<int:pk>/leave/', views.leave_stamp, name='leave_stamp'),
    path("account/", views.account, name="account"),
]
