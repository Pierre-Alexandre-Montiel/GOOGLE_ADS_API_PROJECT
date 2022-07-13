#!/bin/bash
python3 manage.py makemigrations ex
python3 manage.py migrate
python3 manage.py collectstatic 
gunicorn -c gunicorn.conf rush.wsgi
nginx -s reload

