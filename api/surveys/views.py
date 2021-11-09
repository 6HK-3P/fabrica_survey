from datetime import datetime
from functools import cached_property

from django.shortcuts import get_object_or_404
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from surveys.models import Survey, SurveyResult, Question
from surveys.serializers import (SurveySerializer, SurveyUpdateSerializer, SurveyResultSerializer,
                                 QuestionPolymorphicSerializer)


class SurveyViewSet(ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            self.serializer_class = SurveyUpdateSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(start_at__lte=datetime.now(), end_at__gte=datetime.now())
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = []
        return super().get_permissions()


class QuestionViewSet(ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionPolymorphicSerializer
    permission_classes = [IsAuthenticated]

    @cached_property
    def survey(self):
        return get_object_or_404(Survey.objects.filter(id=self.kwargs.get('survey_pk')))

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(survey=self.survey)
        return queryset

    def perform_create(self, serializer):
        serializer.save(survey=self.survey)


class SurveyResultViewSet(CreateModelMixin, RetrieveModelMixin, ListModelMixin, GenericViewSet):
    queryset = SurveyResult.objects.all()
    serializer_class = SurveyResultSerializer
    permission_classes = [IsAuthenticated]

    @cached_property
    def survey(self):
        return get_object_or_404(Survey.objects.filter(id=self.kwargs.get('survey_pk'), start_at__lte=datetime.now(),
                                                       end_at__gte=datetime.now()))

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(survey=self.survey)
        return queryset

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = []
        return super().get_permissions()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.kwargs:
            context.update({
                'survey': self.survey
            })
        return context

    def perform_create(self, serializer):
        serializer.save(survey=self.survey)
