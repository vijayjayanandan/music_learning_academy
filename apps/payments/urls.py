from django.urls import path
from . import views

urlpatterns = [
    path("pricing/", views.PricingView.as_view(), name="pricing"),
    path("checkout/plan/<int:plan_id>/", views.CheckoutView.as_view(), name="checkout-plan"),
    path("checkout/course/<slug:course_slug>/", views.CheckoutView.as_view(), name="checkout-course"),
    path("subscriptions/", views.MySubscriptionsView.as_view(), name="my-subscriptions"),
    path("subscriptions/<int:pk>/", views.SubscriptionDetailView.as_view(), name="subscription-detail"),
    path("subscriptions/<int:pk>/cancel/", views.CancelSubscriptionView.as_view(), name="cancel-subscription"),
    path("history/", views.PaymentHistoryView.as_view(), name="payment-history"),
    path("invoice/<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice-detail"),
    path("coupons/", views.CouponManageView.as_view(), name="coupon-manage"),
    path("payouts/", views.InstructorPayoutListView.as_view(), name="payout-list"),
    path("packages/", views.MyPackagesView.as_view(), name="my-packages"),
    path("packages/<int:pk>/purchase/", views.PackagePurchaseView.as_view(), name="package-purchase"),
    path("tiers/", views.AcademyTierView.as_view(), name="academy-tiers"),
]
