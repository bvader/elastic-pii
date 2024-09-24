
## Introduction:

The prevalence of high-entropy logs in distributed systems has significantly raised the risk of PII (Personally Identifiable Information) seeping into our logs, which can result in security and compliance issues. This 2-part blog delves into the crucial task of identifying and managing this issue using Elasticsearch. We will explore using NLP (Natural Language Processing) and Pattern matching to detect, assess, and, where feasible, redact PII from logs that are being ingested into Elasticsearch.

In **Part 1** of this blog, that can be found [here](https://www.elastic.co/observability-labs/blog/pii-ner-regex-assess-redact-part-1) on the [Elastic Observability Labs](https://www.elastic.co/observability-labs) we will cover the following:

* Review the techniques and tools we have available manage PII in our logs
* Understand the roles of NLP / NER in PII detection
* Build a composable processing pipeline to detect and assess PII
* Sample logs and run them through the NER Model
* Assess the results of the NER Model 

In **Part 2** of this blog (Coming Soo), we will cover the following:

* Redact PII using NER and the redact processor
* Apply field-level security to control access to the un-redacted data
* Enhance the dashboards and alerts
* Production considerations and scaling
* How to run these processes on incoming or historical data