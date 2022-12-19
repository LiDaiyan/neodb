# Modify this Procfile to fit your needs
web: gunicorn neodb.wsgi
rq: python manage.py rqworker --with-scheduler doufen export mastodon
