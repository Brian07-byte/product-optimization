from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pricing/', views.pricing, name='pricing'),
    path('subscription_payment/', views.subscription_payment, name='subscription_payment'),
    path('dashboard/<int:user_id>/', views.dashboard, name='dashboard'),
    path('analyze-file/', views.analyze_file, name='analyze_file'),
    path('submit_data/', views.submit_data, name='submit_data'),
]