# django-production

Opinionated one-size-fits-most defaults for running Django to production (or any other deployed environment).

## Installation

```
pip install django-production
DJANGO_SETTINGS_MODULE=yourproject.settings django-production-apply
```

## What it does

When you install the package, it will install the following dependencies:

* `whitenoise` - for serving static files
* `django-environ` - for reading settings from environment variables
* `django-webserver[gunicorn]` - for running the webserver via `manage.py`
* `django-alive` - for a health check endpoint at `/-/alive/`

Running `django-production-apply` will append the `django-production` settings to your project's settings file and add the healthcheck endpoint to your project's `urlpatterns`. You can see the settings that are added in [settings.py](https://github.com/lincolnloop/django-production/blob/main/django_production/settings.py).

You should add `django-production` to your requirements to keep the necessary dependencies in place. Alternatively, once the patch is applied, you're free to move the dependencies into your own requirements file and remove `django-production` altogether.

By default, static files are loaded from apps and the `static` directory in your project. When building the project for deployment, you should run `manage.py collectstatic --noinput` to collect static files into the `static_collected` directory. In production, `whitenoise` will serve the files in that directory. Be sure you use the [`{% static %}` template tag](https://docs.djangoproject.com/en/dev/ref/templates/builtins/#static) in your templates so you can take advantage of the `Cache-Control` header that `whitenoise` applies. You'll probably want to add `static_collected` to your `.gitignore` (or similar) file.

## Running in production

### Mac OS/Linux

Start the webserver with `python manage.py gunicorn`.

Set the `WEB_CONCURRENCY` environment variable to the number of gunicorn workers you want to run. Start with 2x the number of CPU cores.

### Windows

Start the webserver with `python manage.py waitress --port=8000`.

### Required environment variables

* `DJANGO_ENV` - set to `production` to enable production settings
* `SECRET_KEY` - a secret key for your project

### Optional environment variables when using `DJANGO_ENV=production`

* `ALLOWED_HOSTS` - a comma-separated list of allowed hosts
* `DEBUG` - defaults to `False` you probably don't want to change that
* `DATABASE_URL` - a database URL (see https://django-environ.readthedocs.io/en/latest/types.html#environ-env-db-url)
* `CACHE_URL` or `REDIS_URL` - a cache URL (see https://django-environ.readthedocs.io/en/latest/types.html#environ-env-cache-url)
* `SECURE_HSTS_INCLUDE_SUBDOMAINS` - set this to `True` if your site doesn't have any subdomains that need to use HTTP

Under the hood, `django-production` uses `django-environ`'s [`FileAwareEnv`](https://django-environ.readthedocs.io/en/latest/tips.html#docker-style-file-based-variables) class to read environment variables. This allows you to append `_FILE` to any environment variable to load the value from a file. For example, `DATABASE_URL_FILE=/var/run/secrets/DATABASE_URL` will load the database URL from that file.

## Answers

You didn't ask any questions, but if you did, maybe it would be one of these:

**Why did you write this?**  
Django takes an un-opinionated approach to how it should be deployed. This makes it harder for new users. Even experienced users probably copy this from project-to-project. This aims to make it easy to get a project ready to deploy. I also hope it will give us a chance to create some consensus around these settings as a community and maybe start folding some of this into Django itself.

**Why are you writing to my settings file? You could just just do an import.**
1. It makes it easier to see the changes. I'm of the opinion that settings files should be as simple as possible. Having the settings right there makes it easier to debug.
2. A one-size-fits-all approach will never work here. I'm shooting for one-size-fits-most. Users are free to make changes however they see fit once the change is applied. It's basically what `startproject` is already doing.

**I disagree with the settings/packages you're using.**  
Not a question, but ok. Feel free to submit an issue or pull request with your suggestion and reasoning. We appreciate the feedback and contributions. We may not accept changes that we don't feel fit the spirit of this project (remember, it's _opinionated_). If you're unsure, don't hesitate to ask.

## Publishing a new version

1. Update the version in `django_production/__init__.py`
2. Update the changelog in `CHANGELOG.md`
3. Commit the changes
4. Tag the commit with the version number (`git tag -s v0.9.9 -m v0.9.9`)
5. Push the commit and tag (`git push && git push --tags`)
6. Publish to PyPI `flit publish`

## To Do

* Handle media settings for common object stores
* Email settings including non-SMTP backends like SES