# SMART Project

SMART is a framework for enabling smart decision making and scheduling of live migration.

### Prerequisites


```
Python 3.6.7
```

```
Ansible 
```

### Installing

Activate virtual env


```
pipenv shell
```

Install prerequisites

```
pipenv install
```

Install Ansible

```
sudo apt-get install software-properties-common
sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update
sudo apt-get install ansible
```

## Deployment

Run celery worker


```
celery -A mirai_project worker -l info
```

Run Django


```
python manage.py runserver
```


## Shutdown

Shutdown celery worker


```
celery -A mirai_project control shutdown
```

Clean celery queues


```
killall celery
celery -A mirai_project  purge -f
```

## Built With

* [Django](https://www.djangoproject.com/) - The web framework used
* [DRF](https://www.django-rest-framework.org/) - Used to generate REST API
* [Pipenv](https://pipenv.readthedocs.io/en/latest/) - Dependency Management


## Authors
* **Rami Akrem Addad** - *Initial work, system level optimization, SFC migration schemes designer* - [ramy150](https://github.com/ramy150)

