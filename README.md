---
title: "Using NLP and Pattern Matching to Detect, Assess, and Redact PII in Logs - Part 1"
slug: "pii-ner-regex-assess-redact-part-1"
date: "2024-09-19"
description: "How to detect and assess PII in your logs using NLP"
author:
  - slug: stephen-brown
image: "pii-ner-regex-assess-redact-part-1.png"
tags:
  - slug: log-analytics
  - slug: security
---
## Introduction:

The prevalence of high-entropy logs in distributed systems has significantly raised the risk of PII (Personally Identifiable Information) seeping into our logs, which can result in security and compliance issues. This 2-part blog delves into the crucial task of identifying and managing this issue. We will explore using NLP (Natural Language Processing) and Pattern matching to detect, assess, and, where feasible, redact PII.  

In Part 1 of this blog, we will cover the following:

* Review the techniques and tools we have available
* Understand NLP / NER Role in PII Detections  
* Sample logs and run them through the NER Model 
* Assess the results of the NER Model 

In Part 2 of this blog, we will cover the following:

* Redact PII using NER and redact Processor
* Apply Field Level Security to Control Access to the Un-Redacted Data
* Enhance the Dashboards and Alerts
* Production considerations

Here is the overall flow we will construct over the 2 blogs:

![PII Overall Flow](/assets/images/pii-ner-regex-assess-redact-part-1/pii-overall-flow.png)

All code for this exercise can be found at:
[https://github.com/bvader/elastic-pii](https://github.com/bvader/elastic-pii). 

Loading Data instructions can be found [Data Loading](#data-loading) 

## Tools and Techniques

There are three general capabilities that we will use for this exercise. 

* Named Entity Recognition Detection (NER)
* Pattern Matching Detection
* Log Sampling
* Ingest Pipelines as Composable Processing 


#### Named Entity Recognition (NER) Detection

NER is a sub-task of Natural Language Processing (NLP) that involves identifying and categorizing named entities in unstructured text into predefined categories such as:

* Person: Names of individuals, including celebrities, politicians, and historical figures.
* Organization: Names of companies, institutions, and organizations.
* Location: Geographic locations, including cities, countries, and landmarks.
* Event: Names of events, including conferences, meetings, and festivals.

For our use PII case, we will choose a small optimized NER model [distilbert-NER](https://huggingface.co/dslim/distilbert-NER) that can be downloaded from [Hugging Face](https://huggingface.co) and loaded into Elasticsearch as a trained model. (TODO) talk about tradeoffs, go back (TODO) go back to base

**NOTE: It is important to note that NER / NLP Models are CPU-intensive and expensive to run at scale;** thus, we will want to employ a sampling technique to understand the risk in our logs without sending the full logs volume through the NER Model.


#### Pattern Matching Detection 

In addition to using an NER, regex pattern matching is a powerful tool for detecting and redacting PII based on common patterns. The Elasticsearch [redact](https://www.elastic.co/guide/en/elasticsearch/reference/current/redact-processor.html) processor is built for this use case.


#### Log Sampling

Considering the performance implications of NER and the fact that we may be ingesting a large volume of logs into Elasticsearch, it makes sense to sample our incoming logs. We will build a simple log sampler to accomplish this. 


#### Ingest Pipelines as Composable Processing 

We will create several pipelines, each focusing on a specific capability and a main ingest pipeline to orchestrate the overall process. 

## Building the Processing Flow 

#### Logs Sampling + Composable Ingest Pipelines

The first thing we will do is set up a sampler to sample our logs. This ingest pipeline simply takes a sampling rate between 0 (no log) and 10000 (all logs), which allows as low as ~0.01% sampling rate and marks the sampled logs with `sample.sampled: true`. Further processing on the logs will be driven by the value of `sample.sampled`. The sample.sample_rate can be set here or "passed in" from the orchestration pipeline.

The command should be run from the Kibana -> Dev Tools

Code can be found here for the following three sections. 


<details open>
  <summary>logs-sampler pipeline code - click to collapse</summary>
```
DELETE _ingest/pipeline/logs_sampler
PUT _ingest/pipeline/logs_sampler
{
  "processors": [
    {
      "set": {
        "description": "Set Sampling Rate 0 None 10000 all allows for 0.01% precision",
        "if": "ctx.sample.sample_rate == null",
        "field": "sample.sample_rate",
        "value": 10000
      }
    },
    {
      "set": {
        "description": "Determine if keeping unsampled docs",
        "if": "ctx.sample.keep_unsampled == null",
        "field": "sample.keep_unsampled",
        "value": true
      }
    },
    {
      "set": {
        "field": "sample.sampled",
        "value": false
      }
    },
    {
      "script": {
        "source": """ Random r = new Random();
        ctx.sample.random = r.nextInt(params.max); """,
        "params": {
          "max": 10000
        }
      }
    },
    {
      "set": {
        "if": "ctx.sample.random <= ctx.sample.sample_rate",
        "field": "sample.sampled",
        "value": true
      }
    },
    {
      "drop": {
         "description": "Drop unsampled document if applicable",
        "if": "ctx.sample.keep_unsampled == false && ctx.sample.sampled == false"
      }
    }
  ]
}
```
</details>

Now, let's test the logs sampler. We will build the first part of the composable pipeline. We will be sending logs to the logs-generic-default data stream. With that in mind, we will create the `logs@custom` ingest pipeline that will be automatically called using the logs [data stream framework](https://www.elastic.co/guide/en/fleet/current/data-streams.html#data-streams-pipelines) for customization. We will add one additional level of abstraction so that you can apply this PII processing to other data streams.

Next, we will create the process-pii pipeline. This is the core processing pipeline where we will orchestrate PII processing component pipelines. In this first step, we will simply apply the sampling logic. Note that we are setting the sampling rate to 100, which is equivalent to 1.0% of the logs.

<details open>
  <summary>process-pii pipeline code - click to collapse</summary>
```
# Process PII pipeline - part 1
DELETE _ingest/pipeline/process-pii
PUT _ingest/pipeline/process-pii
{
  "processors": [
    {
      "set": {
        "description": "Set true if enabling sampling, otherwise false",
        "field": "sample.enabled",
        "value": true
      }
    },
    {
      "set": {
        "description": "Set Sampling Rate 0 None 10000 all allows for 0.01% precision",
        "field": "sample.sample_rate",
        "value": 1000
      }
    },
    {
      "set": {
        "description": "Set to false if you want to drop unsampled data, handy for reindexing hostorical data",
        "field": "sample.keep_unsampled",
        "value": true
      }
    },
    {
      "pipeline": {
        "if": "ctx.sample.enabled == true",
        "name": "logs-sampler",
        "ignore_failure": true
      }
    }
  ]
}
```
</details>

Finally, we create the logs `logs@custom`, which will simply call our `process-pii` pipeline based on the correct `data_stream.dataset`

<details open>
  <summary>logs@custom pipeline code - click to collapse</summary>
```
DELETE _ingest/pipeline/logs@custom
PUT _ingest/pipeline/logs@custom
{
  "processors": [
    {
      "set": {
        "field": "pipelinetoplevel",
        "value": "logs@custom"
      }
    },
        {
      "set": {
        "field": "pipelinetoplevelinfo",
        "value": "{{{data_stream.dataset}}}"
      }
    },
    {
      "pipeline": {
        "description" : "Call the process_pii pipeline on the correct dataset",
        "if": "ctx?.data_stream?.dataset == 'pii'", 
        "name": "process_pii"
      }
    }
  ]
}
```
</details>

Now, let's test to see the sampling at work.

Load the data as described here [Data Loading](#data-loading). Let's use the sample data first, and we will talk about how to test with your incoming or historical logs later at the end of this blog. 

If you look at Discover with KQL filter `data_stream.dataset : pii` and Breakdown by sample.sampled, you should see the breakdown to be approximately 10%

![PII Discover 1](/assets/images/pii-ner-regex-assess-redact-part-1/pii-discover-1-part-1.png)


At this point we have a composable ingest pipeline that is "sampling" logs. As a bonus, you can use this logs sampler for any other use cases you have as well. 

#### Loading, Configuration, and Execution of the NER Pipeline


##### Loading the NER Model


You will need a Machine Learning node to run the NER model on. In this exercise, we are using [Elastic Cloud Hosted Deployment ](https://www.elastic.co/guide/en/cloud/current/ec-getting-started.html)on AWS with the [CPU Optimized (ARM)](https://www.elastic.co/guide/en/cloud/current/ec_selecting_the_right_configuration_for_you.html) architecture. The NER inference will run on a Machine Learning AWS c5d node. There will be GPU options in the future, but today, we will stick with CPU architecture.  

This exercise will use a single c5d with 16GB and 8.4 vCPU. 


Please refer to the official documentation on [how to import an NLP-trained model into Elasticsearch](https://www.elastic.co/guide/en/machine-learning/current/ml-nlp-import-model.html) for complete instructions on uploading, configuring, and deploying the model.

The quickest way to get the model is using the Eland Docker method. 
 
The following command will load the model into Elasticsearch but will not start it. We will do that in the next step.  

```
docker run -it --rm --network host docker.elastic.co/eland/eland \
  eland_import_hub_model \
  --url https://my-deployment.es.us-west-1.aws.found.io:443/ \
  -u elastic -p <password> \
  --hub-model-id dslim/bert-base-NER \
  --task-type ner
```

#####
Deploy and Start the NER Model

In general, to improve ingest performance, increase throughput by adding more allocations to the deployment. For improved search speed, increase the number of threads per allocation.

To scale ingest, we will focus on scaling the allocations for the deployed model. More information on this topic is available [here](https://www.elastic.co/guide/en/machine-learning/current/ml-nlp-deploy-model.html). The number of allocations must be less than the available allocated processors (cores, not vCPUs) per node. (THIS IS NOT TRUE TODO)


(TODO) NER Performance metrics are based on the dataset being used for this exercise.

To deploy and start the NER Model. We will do this using the [Start trained model deployment API](https://www.elastic.co/guide/en/elasticsearch/reference/8.15/start-trained-model-deployment.html)

We will configure



* 8 Allocations to allow for more parallel ingestion
* 1 Thread per Allocation
* 0 Byes Cache, as we expect a low cache hit rate 
* 8192 Queue

 (TODO fix with full Model)

```
# 8 Allocators x 1 Thread, 0 Cache, Queue 8192
POST _ml/trained_models/dslim__distilbert-ner/deployment/_start?cache_size=0b&number_of_allocations=8&threads_per_allocation=1&queue_capacity=8192
```


You should get a response that looks something like this. (TODO fix with full Model)

```
{
  "assignment": {
    "task_parameters": {
      "model_id": "dslim__distilbert-ner",
      "deployment_id": "dslim__distilbert-ner",
      "model_bytes": 260831330,
      "threads_per_allocation": 1,
      "number_of_allocations": 8,
      "queue_capacity": 8192,
      "cache_size": "0",
      "priority": "normal",
      "per_deployment_memory_bytes": 260795428,
      "per_allocation_memory_bytes": 544331848
    },
    …
}
```



The NER model has been deployed and started and is ready to be used.



##### Execute NER Inference Model

The following ingest pipeline implements the NER model via the [inference](https://www.elastic.co/guide/en/elasticsearch/reference/current/inference-processor.html) processor. 

There is a significant amount of code here, but only two items of interest now exist. The rest of the code is conditional logic to drive some additional specific behavior that we will look closer at in the future. 



1. The inference processor calls the NER model by ID, which we loaded previously, and passes the text to be analyzed, which, in this case, is the message field, which is the text_field we want to pass to the NER model to analyze for PII.

2. The script processor loops through the message field and uses the data generated by the NER model to replace the identified PII with redacted placeholders. This looks more complex than it really is, as it simply loops through the array of ML predictions and replaces them in the message string with constants, and stores the results in a new field `redact.message`. We will look at this a little closer in the following steps. 

The Complete Code. 


The NER PII Pipeline
 (TODO fix with full Model)
```
PUT _ingest/pipeline/logs_ner_pii_processor
{
  "processors": [
    {
      "set": {
        "description": "Set to true to actually redact, false will run processors but leave original",
        "field": "redact.enable",
        "value": true
      }
    },
    {
      "set": {
        "description": "Set to true to keep ml results for debugging",
        "field": "redact.ner.keep_result",
        "value": true
      }
    },
    {
      "set": {
        "description": "Set to PER, LOC, ORG to skip, or NONE to not drop any replacement",
        "field": "redact.ner.skip_entity",
        "value": "NONE"
      }
    },
    {
      "set": {
        "description": "Set to PER, LOC, ORG to skip, or NONE to not drop any replacement",
        "field": "redact.ner.minimum_score",
        "value": 0.0
      }
    },
    {
      "set": {
        "if" : "ctx.redact.message == null",
        "field": "redact.message",
        "copy_from": "message"
      }
    },
    {
      "set": {
        "field": "redact.successful",
        "value": true
      }
    },
    {
      "inference": {
        "model_id": "dslim__distilbert-ner",
        "field_map": {
          "message": "text_field"
        },
        "on_failure": [
          {
            "set": {
              "description": "Set 'error.message'",
              "field": "failure",
              "value": "REDACT_NER_FAILED"
            }
          },
          {
            "set": {
              "field": "redact.successful",
              "value": false
            }
          }
        ]
      }
    },
    {
      "script": {
        "if": "ctx.failure_ner != 'REDACT_NER_FAILED'",
        "lang": "painless",
        "source": """String msg = ctx['message'];
          for (item in ctx['ml']['inference']['entities']) {
            if ((item['class_name'] != ctx.redact.ner.skip_entity) && 
              (item['class_probability'] >= ctx.redact.ner.minimum_score)) {  
                msg = msg.replace(item['entity'], '<' + 
                'REDACTNER-'+ item['class_name'] + '>')
            }
          }
          ctx.redact.message = msg""",
        "on_failure": [
          {
            "set": {
              "description": "Set 'error.message'",
              "field": "failure",
              "value": "REDACT_REPLACEMENT_SCRIPT_FAILED",
              "override": false
            }
          },
          {
            "set": {
              "field": "redact.successful",
              "value": false
            }
          }
        ]
      }
    },
    {
      "remove": {
        "if": "ctx.redact.ner.keep_result != true",
        "field": [
          "ml"
        ],
        "ignore_missing": true,
        "ignore_failure": true
      }
    }
  ],
  "on_failure": [
    {
      "set": {
        "field": "failure",
        "value": "GENERAL_FAILURE",
        "override": false
      }
    }
  ]
}

```


And the Updated PII Processor Pipeline, which now calls the NER Pipeline

```
PUT _ingest/pipeline/process_pii
{
  "processors": [
    {
      "set": {
        "description": "Set true if enabling sampling, otherwise false",
        "field": "sample.enabled",
        "value": true
      }
    },
    {
      "set": {
        "description": "Set Sampling Rate 0 None 10000 all allows for 0.01% precision",
        "field": "sample.sample_rate",
        "value": 5000
      }
    },
    {
      "set": {
        "description": "Set to false if you want to drop unsampled data, handy for reindexing hostorical data",
        "field": "sample.keep_unsampled",
        "value": true
      }
    },
    {
      "pipeline": {
        "if": "ctx.sample.enabled == true",
        "name": "log_sampler",
        "ignore_failure": true
      }
    },
    {
      "set": {
        "description" : "Make a copy of the message field to work on",
        "if": "ctx.sample.enabled == false || (ctx.sample.enabled == true && ctx.sample.sampled == true)",
        "field": "redact.message",
        "copy_from": "message"
      }
    },
    {
      "pipeline": {
        "if": "ctx.sample.enabled == false || (ctx.sample.enabled == true && ctx.sample.sampled == true)",
        "name": "logs_ner_pii_processor"
      }
    }
  ]
}

```


**TODO: Now Reload the data as described here (Link to loading data)***

Let's take a look at the results. In the Discover KQL query bar, execute the following query
`data_stream.dataset : pii and ml.inference.entities.class_name : ("PER" and "LOC" and "ORG" )` 

Discover should look something like this

![PII Discover 2](/assets/images/pii-ner-regex-assess-redact-part-1/pii-discover-2-part-1.png)


 if you inspect the details of one of the documents, you should see the following. 

Let's look at a few of these fields in a little more detail. 

Todo


## Code

Navigate to

[https://github.com/bvader/elastic-pii](https://github.com/bvader/elastic-pii)

```
$ git clone https://github.com/bvader/elastic-pii.git
```

## Data Loading


#### Creating and Loading the Sample Data Set 

```
$ cd python
$ python -m venv .env
$ source .env/bin/activate
$ pip install elasticsearch
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
and run 

```
$ python load_logs.py
```

#### Assesing Your Incoming Logs 


#### Assessing Your Historical Logs
