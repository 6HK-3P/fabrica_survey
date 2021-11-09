from html import unescape

from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator
from polymorphic.models import PolymorphicModel

from survey.models import NON_POLYMORPHIC_CASCADE


class Survey(models.Model):
    name = models.CharField(max_length=255, verbose_name='название')
    description = models.TextField('описание')
    start_at = models.DateTimeField('дата начала')
    end_at = models.DateTimeField('дата окончания')

    class Meta:
        verbose_name = 'опрос'
        verbose_name_plural = 'опросы'

    def __str__(self):
        return self.name

    def clean(self):
        if self.start_at > self.end_at:
            raise ValidationError('Опрос не может закончиться до того, как начнется')

    def is_started(self):
        return timezone.now() > self.start_at

    def is_ended(self):
        return timezone.now() > self.end_at


class Answer(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    question = GenericForeignKey()
    text = models.TextField('текст ответа')

    class Meta:
        verbose_name = 'ответ'
        verbose_name_plural = 'ответы'

    def __str__(self):
        return strip_tags(unescape(Truncator(self.text).words(20, html=True, truncate=' …')))

# Questions

class Question(PolymorphicModel):
    survey = models.ForeignKey(Survey, on_delete=NON_POLYMORPHIC_CASCADE, related_name='questions',
                               verbose_name='опрос')

    text = models.TextField('текст вопроса')

    def __str__(self):
        return strip_tags(unescape(Truncator(self.text).words(20, html=True, truncate=' …')))


class InputQuestion(Question):
    class Meta(Question.Meta):
        verbose_name = 'вопрос с пользовательским вводом'
        verbose_name_plural = 'вопросы с пользовательским вводом'


class BaseChoiceQuestion(Question):
    answers = GenericRelation(Answer)

    class Meta(Question.Meta):
        abstract = True


class ChoiceQuestion(BaseChoiceQuestion):
    class Meta(Question.Meta):
        verbose_name = 'вопрос с одиночным выбором'
        verbose_name_plural = 'вопросы с одиночным выбором'


class MultiChoiceQuestion(BaseChoiceQuestion):
    class Meta(Question.Meta):
        verbose_name = 'вопрос с множественным выбором'
        verbose_name_plural = 'вопросы с множественным выбором'


# User answers

class SurveyResult(models.Model):
    user = models.IntegerField(verbose_name='пользователь')
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, verbose_name='опрос', related_name='results')

    class Meta:
        verbose_name = 'результат'
        verbose_name_plural = 'результаты'
        unique_together = ['user', 'survey']

    def __str__(self):
        return self.survey.__str__()


class UserAnswer(PolymorphicModel):
    result = models.ForeignKey(SurveyResult, on_delete=models.CASCADE, verbose_name='результат', related_name='answers')

    class Meta:
        verbose_name = 'ответ пользователя'
        verbose_name_plural = 'ответы пользователя'


class UserInputAnswer(UserAnswer):
    question = models.ForeignKey(InputQuestion, on_delete=models.CASCADE, related_name='user_answers',
                                 verbose_name='вопрос')

    text = models.TextField('текст')

    def __str__(self):
        return self.text


class UserChoiceAnswer(UserAnswer):
    question = models.ForeignKey(ChoiceQuestion, on_delete=models.CASCADE, related_name='user_answers',
                                 verbose_name='вопрос')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='user_choices', verbose_name='ответ')

    def __str__(self):
        return self.answer.text


class UserMultiChoiceAnswer(UserAnswer):
    question = models.ForeignKey(MultiChoiceQuestion, on_delete=models.CASCADE, related_name='user_answers',
                                 verbose_name='вопрос')
    answers = models.ManyToManyField(Answer, related_name='user_multi_choices', verbose_name='ответы')

    def __str__(self):
        if not self.pk:
            return '-'
        return ', '.join(self.answers.values_list('text', flat=True))
