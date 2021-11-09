from django.db import transaction
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, Serializer
from rest_polymorphic.serializers import PolymorphicSerializer

from surveys.models import (Question, Answer, ChoiceQuestion, MultiChoiceQuestion, InputQuestion, Survey,
                            UserInputAnswer, UserAnswer, UserChoiceAnswer, UserMultiChoiceAnswer, SurveyResult)


class AnswerSerializer(ModelSerializer):
    class Meta:
        model = Answer
        extra_kwargs = {
            'id': {'read_only': False, 'required': False}
        }
        exclude = ['content_type', 'object_id']


class QuestionSerializer(ModelSerializer):
    class Meta:
        model = Question
        exclude = ['polymorphic_ctype']
        read_only_fields = ['survey']


class ChoiceQuestionSerializerMixin(Serializer):
    answers = AnswerSerializer(many=True)

    def validate_answers(self, answers):
        if not len(answers):
            raise ValidationError('Это поле обязательно.')
        return answers

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        with transaction.atomic():
            instance = super().create(validated_data)
            self.create_answers(instance, answers_data)
        return instance

    def create_answers(self, instance, answers):
        Answer.objects.bulk_create([Answer(**answer, question=instance) for answer in answers])

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', {})
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            self.update_answers(instance, answers_data)
        return instance

    def update_answers(self, instance, answers):
        for answer in answers:
            id = answer.pop('id', None)
            if id:
                Answer.objects.filter(id=id).update(**answer)
            else:
                Answer.objects.create(**answer, question=instance)


class InputQuestionSerializer(ModelSerializer):
    class Meta(QuestionSerializer.Meta):
        model = InputQuestion


class ChoiceQuestionSerializer(ChoiceQuestionSerializerMixin, ModelSerializer):
    class Meta(QuestionSerializer.Meta):
        model = ChoiceQuestion


class MultiChoiceQuestionSerializer(ChoiceQuestionSerializerMixin, ModelSerializer):
    class Meta(QuestionSerializer.Meta):
        model = MultiChoiceQuestion


class QuestionPolymorphicSerializer(PolymorphicSerializer):
    resource_type_field_name = 'question_type'
    base_serializer_class = QuestionSerializer
    model_serializer_mapping = {
        InputQuestion: InputQuestionSerializer,
        ChoiceQuestion: ChoiceQuestionSerializer,
        MultiChoiceQuestion: MultiChoiceQuestionSerializer,
    }


class SurveySerializer(WritableNestedModelSerializer):
    questions = QuestionPolymorphicSerializer(many=True, read_only=True)

    class Meta:
        model = Survey
        fields = '__all__'

    def validate(self, attrs):
        data = super().validate(attrs)
        start_at = data.get('start_at', self.instance.start_at)
        if start_at > data.get('end_at'):
            raise ValidationError('Опрос не может закончиться до того, как начнется')
        return data


class SurveyUpdateSerializer(SurveySerializer):
    class Meta:
        model = Survey
        exclude = ['start_at']


class UserAnswerSerializer(ModelSerializer):
    class Meta:
        model = UserAnswer
        exclude = ['polymorphic_ctype']
        read_only_fields = ['result']


class UserInputAnswerSerializer(WritableNestedModelSerializer):
    class Meta(UserAnswerSerializer.Meta):
        model = UserInputAnswer


class UserChoiceAnswerSerializer(WritableNestedModelSerializer):
    class Meta(UserAnswerSerializer.Meta):
        model = UserChoiceAnswer


class UserMultiChoiceAnswerSerializer(WritableNestedModelSerializer):
    class Meta(UserAnswerSerializer.Meta):
        model = UserMultiChoiceAnswer

    def validate(self, attrs):
        if not len(attrs['answers']) >= 1:
            raise ValidationError('Необходим как минимум один ответ')

        return super().validate(attrs)


class UserAnswerPolymorphicSerializer(PolymorphicSerializer, WritableNestedModelSerializer):
    class Meta:
        model = UserAnswer
        fields = '__all__'

    resource_type_field_name = 'user_answer_type'
    base_serializer_class = UserAnswerSerializer
    model_serializer_mapping = {
        UserInputAnswer: UserInputAnswerSerializer,
        UserChoiceAnswer: UserChoiceAnswerSerializer,
        UserMultiChoiceAnswer: UserMultiChoiceAnswerSerializer
    }


class SurveyResultSerializer(WritableNestedModelSerializer):
    answers = UserAnswerPolymorphicSerializer(many=True)

    class Meta:
        model = SurveyResult
        fields = '__all__'
        read_only_fields = ('survey',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.survey = self.context.get('survey')

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if self.survey.results.filter(user=attrs.get('user')).exists():
            raise ValidationError({'survey': 'Вы уже проходили этот опрос'})
        answers = attrs.get('answers')
        if len(answers) < self.survey.questions.count():
            raise ValidationError({'answers': 'Необходимо ответить на все вопросы'})

        return attrs