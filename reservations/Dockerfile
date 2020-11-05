# base image
FROM python:3.6.8-alpine

# Default vars
ENV APP_HOME=/var/app

# Application directory
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

RUN adduser -S -h $APP_HOME -H app

# add requirements
COPY ./requirements.txt $APP_HOME/requirements.txt

# install requirements
RUN pip install -r requirements.txt

# add app
COPY . $APP_HOME

# set user permissions
RUN chown -R app $APP_HOME
USER app

EXPOSE 8080/tcp
CMD [ "gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]
