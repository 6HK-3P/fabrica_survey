from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

from surveys.views import SurveyViewSet, SurveyResultViewSet, QuestionViewSet

router = SimpleRouter()
router.register('surveys', SurveyViewSet)

survey_router = NestedSimpleRouter(router, 'surveys', lookup='survey')
survey_router.register('questions', QuestionViewSet)
survey_router.register('survey_results', SurveyResultViewSet)

app_name = 'surveys'

urlpatterns = [
    *router.urls,
    *survey_router.urls
]
