"""Django urlpatterns declaration for nautobot_device_onboarding app."""

from django.templatetags.static import static
from django.urls import path
from django.views.generic import RedirectView
from nautobot_device_onboarding import views
from nautobot.apps.urls import NautobotUIViewSetRouter

router = NautobotUIViewSetRouter()
router.register("onboardingconfigsyncdevices", views.OnboardingConfigSyncDevicesUIViewSet)

urlpatterns = [
    path("docs/", RedirectView.as_view(url=static("nautobot_device_onboarding/docs/index.html")), name="docs"),
    path("config/", views.OnboardingConfigView.as_view(), name="config"),
]

urlpatterns += router.urls