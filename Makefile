.PHONY:

run-prod:
	FLASK_APP=peer flask run

run-dev:
	PYTHONDONTWRITEBYTECODE=1 FLASK_APP=peer FLASK_ENV=development flask run

clean:
	rm -rf __pycache__
