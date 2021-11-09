# Survey

Система опроса

## Запуск

`docker-compose build` - собрать проект

`docker-compose up` - запустить проект

#### Частая ошибка 
`./entrypoint.sh: 5: set: Illegal option -o errexit` - В этом случае необходимо изменить разрыв строки с `CRLF` на `LF` 
в файле `entrypoint.sh`

## Перед началом работы

Для корректной работы небходимо применить миграции:

`docker-compose run --rm api python manage.py migrate`

Создание администратора системы:

`docker-compose run --rm api python manage.py createsuperuser`

# Документация

## Панель администратора

Доступ к панели доступна по ссылке http://localhost/admin/

## API

Документация к апи доступна по ссылке http://localhost/api/documentation/

### Доступные методы

##### Авторизация в системе

http://localhost/api/token/ - получение токена авторизации

Метод - POST

Обязательные параметры:
* username - имя пользователя
* password - пароль

Ответ:
* access - Токен авторизации
* refresh - Рефреш токен для обновления токена авторизации

После получения токена авторизации его необходимо добавлять в заголовки запроса:
`Authorization: Bearer <access>`

#### Опросы

Все запросы описаны в [документации](http://localhost/api/documentation/#tag/surveys) 

#### Вопросы у опросов

Все запросы описаны в [документации](http://localhost/api/documentation/#tag/surveys-questions)

#### Прохождение опроса

http://localhost/api/surveys/{survey_pk}/survey_results/

Метод - POST

Пример запроса
```
{
    "answers": [
        {
            "user_answer_type": "UserInputAnswer",
            "text": "some text",
            "question": 1
        },
        {
            "user_answer_type": "UserChoiceAnswer",
            "answer": 1,
            "question": 2
        },
        {
            "user_answer_type": "UserMultiChoiceAnswer",
            "answers": [
                2,
                3
            ],
            "question": 3
        }
    ],
    "user": 1
}
```
* `user` - идентификатор пользователя
* `answers` - ответы пользователя
  * `user_answer_type` - Тип вопроса. Всего 3 типа:
    * `UserInputAnswer` - Вопрос с текстовым ответом
    * `UserChoiceAnswer` - Вопрос с выбором одного ответа
    * `UserMultiChoiceAnswer` - Вопрос с возможностью выбрать несколько ответов
  * `text` - текст ответа. Он необходим когда тип вопроса `UserInputAnswer`.
  * `answer` - `id` ответа. Он необходим когда тип вопроса `UserChoiceAnswer`.
  * `answers` - список содержащий `id` ответов.  Он необходим когда тип вопроса `UserMultiChoiceAnswer`.
  * `question` - `id` вопроса.
