# Andres Villalobos
Clinical Data Engineer | Boston, MA | (617) 445-8923 | andres.villalobos@email.com

## Professional Experience

**Clinical Data Engineer** | Meridian Health Systems | Boston, MA | March 2024 – Present

I work within the clinical informatics team to integrate AI-assisted documentation tools into our EHR workflows. My primary responsibility has been implementing and maintaining ETL pipelines that feed de-identified patient data into our LLM-based clinical note summarization system, which is currently used by approximately 120 physicians across three hospital networks. I write Python scripts to extract structured data from HL7 messages, validate the output against data quality thresholds, and monitor pipeline health through CloudWatch dashboards. Recently, I contributed to an integration project that connected our prompt-engineering team's GPT-4 based template recommendations directly into the note composition interface; my role involved building the API middleware and handling edge cases around patient data privacy compliance. The system has reduced average documentation time by roughly 8 minutes per patient encounter in pilot units. I pair regularly with clinicians and IT operations to understand failure modes and iterate on the pipeline—work that has surfaced several bugs in our validation logic and led to two process improvements that reduced data rejection rates. I do not own the system's architecture or on-call responsibilities, but I've become the go-to person for understanding how data flows from our source systems into the model endpoints.

**Junior Software Engineer (Data)** | Vital Diagnostics Inc. | Cambridge, MA | June 2023 – February 2024

I contributed to a cloud-based lab result processing platform that generates automated clinical alerts for abnormal test values. Using AWS Lambda and Python, I built helper functions that normalized incoming lab data from third-party testing vendors and prepared that data for rule evaluation. I also assisted in adding a small exploratory LLM feature that allowed clinicians to query historical lab trends using natural language; this involved writing validation scripts and spot-checking model outputs against expected clinical patterns before the feature moved to limited beta. The platform processes roughly 15,000 lab orders per day and is used by reference laboratories and hospital outpatient centers. While I was not responsible for the core alert engine or the deployment infrastructure, my code changes shipped to production within weeks and have been running stably without needing my intervention. I worked closely with QA engineers to write test cases and collaborated with the product team to clarify requirements for the language interface feature.

## Education

**Bachelor of Science in Computer Science** | University of Massachusetts Amherst | Graduated May 2023

Coursework in database systems, software engineering, and data structures.

## Technical Skills

Python, SQL, AWS (Lambda, S3, CloudWatch), HL7, Git, REST APIs, Basic Prompt Engineering, JSON/XML parsing
