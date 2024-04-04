FROM python:3

RUN apt-get update && apt-get install -y binutils libproj-dev gdal-bin

ENV POETRY_VIRTUALENVS_CREATE=false
RUN pip install poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --no-ansi
COPY . .

EXPOSE 80
CMD gunicorn flatscatalog.wsgi:application --bind 0.0.0.0:80