#### Creating and Loading the Sample Data Set
**NOTE** There is a pre-generated log file `pii.log` if you want to use that. Then you only need to run `load_logs.py`.

```
$ cd elastic-pii
$ cd python
$ python -m venv .env
$ source .env/bin/activate
$ pip install elasticsearch
$ pip install Faker
```

Run the log generator 
```
$ python generate_random_logs.py
```

If you do not changes any parameters, this will create 10000 random logs in a file named pii.log with a mix of logs that containe and do not contain PII. 

Edit `load_logs.py` and set the following 

```
# The Elastic User 
ELASTIC_USER = "elastic"

# Password for the 'elastic' user generated by Elasticsearch
ELASTIC_PASSWORD = "askdjfhasldfkjhasdf"

# Found in the 'Manage Deployment' page
ELASTIC_CLOUD_ID = "deployment:sadfjhasfdlkjsdhf3VuZC5pbzo0NDMkYjA0NmQ0YjFiYzg5NDM3ZDgxM2YxM2RhZjQ3OGE3MzIkZGJmNTE0OGEwODEzNGEwN2E3M2YwYjcyZjljYTliZWQ="
```
Then run the following command. 


```
$ python load_logs.py
```
#### Reloading the logs
**Note** To reload the logs, you can simply re-run the above command. You can run the command multiple time during this exercise and the logs will be reloaded (actually loaded again). The new logs will not collide with previous runs as there will be a unique `run.id` for each run which is displayed at the end of the loading process.

```
$ python load_logs.py
```
