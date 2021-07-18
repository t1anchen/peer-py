#!/bin/sh

echo "dev-start"
PYTHONDONTWRITEBYTECODE=1 \
FLASK_APP=peer \
FLASK_ENV=development \
flask run &
