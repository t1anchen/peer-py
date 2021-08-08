.PHONY:

prod-start:
	FLASK_APP=peer flask run

dev-start:
	./dev-start.sh

dev-stop:
	./dev-stop.sh

e2e-test:
	./client/e2e/test.sh

ci: dev-start
	sleep 5
	rm -vf client.log
	make e2e-test

clean:
	rm -rf __pycache__
