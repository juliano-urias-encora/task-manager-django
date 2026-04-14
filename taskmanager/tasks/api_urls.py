from rest_framework.routers import DefaultRouter

from .api_views import TaskStatusViewSet, TaskViewSet

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename="task")
router.register(r"statuses", TaskStatusViewSet, basename="taskstatus")

urlpatterns = router.urls
