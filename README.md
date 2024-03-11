# ✨ Technical Test - Indy ✨

This project is built on top of the [python-django-drf-boilerplate](https://github.com/Vivify-Ideas/python-django-drf-boilerplate).

I used this simply because that's the technology I'm used to work with, it saved me a lot of time (it would have taken me longer to figure stuff out in NodeJS for example). On the plus side, it comes with a lot of built-in features - it has  Postgres DB, Swagger docs, dockerization etc... see below for full list of features if you're interested (I left it from the original README).


## Starting the application

You will need Docker to run this project - simply check out the repo and run the following command:

```bash
cp .env.dist .env
```

You will need to modify the .env file manually as well, to add the following line:

```OPEN_WEATHER_KEY=[put your key here]```

(I didn't want to commit the key to the repo, hence this extra step for security)

Then run this command to start the container:

```bash
docker-compose up
```

If all goes well, this should start the server, run all the migrations etc...


## Test the API with Swagger

Now the server is up and running, you should be able to access the Swagger docs via [link](http://localhost:8001/swagger)

However, you may run into a 403 error: this means you need to authenticate first. To do this, create a superuser first, by running the following command:

```bash
docker-compose run --rm web ./manage.py createsuperuser
```

Then open the Django admin: [link](http://localhost:8001/admin)
Authenticate on the admin page. Once authenticated, you should be able to access swagger.

You will find several endpoints, thought the 2 we are interested in which I created are:
- /api/v1/promocodes/
- /api/v1/promocodes/validate

Happy testing!


## Run the unit tests

Simply run the command:

```bash
docker-compose run --rm web ./manage.py test
```

Nothing special here, the tests should all pass.

A quick note: test coverage is not 100%, I didn't have time to fully complete this but hopefully this gives you a good idea of the intention. I also didn't write integration test for the API view, only wrote unit tests, but likewise, this was just a question of time.


## Code improvements

I left many TODO comments in the code. I ran out of time, so the code is not perfect by any means. For example some of the logic inside the view may belong inside the serializer, and likewise some of the logic might belong in the models.

Some of the code could also do with some refactoring to improve readability, making it DRY etc...

The function that validates the promo code was obviously the biggest challenge. I wrote it as a recursive function which calls itself when encountering an or/and statement. The code is not particularly pretty, like I said this could do with some refactoring to make it more readble.


## Boilerplate
Below is some info about the boilertplate I used, its features etc...

### Boilerplate - Highlights

- Modern Python development with Python 3.8+
- Bleeding edge Django 3.1+
- Fully dockerized, local development via docker-compose.
- PostgreSQL
- Full test coverage, continuous integration, and continuous deployment.
- Celery tasks

### Boilerplate - Features built-in

- JSON Web Token authentication using [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/)
- Social (FB + G+) signup/sigin
- API Throttling enabled
- Password reset endpoints
- User model with profile picture field using Easy Thumbnails
- Files management (thumbnails generated automatically for images)
- Sentry setup
- Swagger API docs out-of-the-box
- Code formatter [black](https://black.readthedocs.io/en/stable/)
- Tests (with mocking and factories) with code-coverage support
