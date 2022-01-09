web: gunicorn stockmarket.wsgi:application --timeout 30 --log-file - --log-level debug
python manage.py collectstatic --noinput
release: python manage.py migrate
