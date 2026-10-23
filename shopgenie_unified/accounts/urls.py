from django.urls import path
from .views import LoginView, RegisterCustomerView, RegisterOwnerView, RefreshTokenView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/customer/", RegisterCustomerView.as_view(), name="register-customer"),
    path("register/owner/", RegisterOwnerView.as_view(), name="register-owner"),
    path("refresh/", RefreshTokenView.as_view(), name="refresh-token"),
]