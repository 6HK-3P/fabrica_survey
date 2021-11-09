FROM python:3.9

# initial

EXPOSE 80

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=80

WORKDIR /api/

# install pipenv

RUN pip install pipenv==2020.11.15

# install dependencies

COPY ./Pipfile* ./

RUN pipenv install --system --deploy --dev

# copy project

COPY . ./

# entrypoint setup

RUN chmod +x "./entrypoint.sh"

ENTRYPOINT ["sh", "./entrypoint.sh"]

# final

CMD ["uwsgi", "./config/uwsgi.ini"]
