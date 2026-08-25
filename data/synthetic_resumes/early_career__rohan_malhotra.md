# Rohan Malhotra
Software Engineer, E-commerce Platform
rohan.malhotra@emailbox.com | (412) 556-8847 | LinkedIn.com/in/rohanmalhotra | Pittsburgh, PA

## Professional Experience

**Software Engineer, CartFlow Systems** | Pittsburgh, PA | March 2024 – Present

I work on the backend services team supporting CartFlow's e-commerce platform, which processes roughly 50,000 orders weekly across multiple retail verticals. My primary responsibility is maintaining and extending the product recommendation engine that surfaces personalized items to logged-in customers on category pages and in post-purchase emails. The system was already in production when I joined, but I've contributed several meaningful improvements. I refactored the recommendation API's caching layer to reduce average response latency from 320ms to 180ms, which improved page load metrics for roughly 15% of traffic. I also built out the instrumentation and logging for the recommendation service to better track cache hit rates and model inference timing, making it easier for the team to debug performance issues in production. Recently, I integrated a smaller LLM-based product bundling feature that suggests complementary items to customers during checkout; this feature runs inference through an external API and returns suggestions within the strict latency budget required by the checkout flow. The bundling logic itself is straightforward—ranking and filtering results—but it required coordination with the API provider and careful integration into the payment pipeline to avoid blocking transactions. I've contributed to two quarterly releases and participated in a service incident where a database connection pool exhaustion affected the recommendation service for roughly two hours; while I didn't drive the incident response, I helped trace the root cause and implemented additional monitoring to prevent similar issues.

**Junior Software Engineer, Nexus Retail Technologies** | Columbus, OH | August 2023 – February 2024

At Nexus Retail, I was part of a small team building internal tooling for warehouse management and inventory visibility. I joined the team shortly after we launched an inventory sync service that connected our e-commerce front end with regional fulfillment centers. Most of my work involved adding new data fields and endpoints to that service as business requirements evolved. I built out the API logic to surface real-time stock levels across locations, which involved querying multiple backend systems and aggregating results into a single response. I also contributed to adding warehouse-specific metadata to our database schema and wrote the migration scripts to backfill historical data. The work wasn't glamorous—a lot of it was defensive coding and careful testing—but it was necessary to support the sales team's ability to view inventory accurately. I took on a short project to evaluate whether we could use an LLM to help automatically categorize incoming product attributes from vendor data feeds. I prototyped a solution using prompt engineering and explored a few different API providers, but ultimately the accuracy wasn't sufficient for production, so the project was shelved in favor of a more traditional ML classifier. Still, the exercise taught me how to work with LLM APIs and think about their strengths and limitations. I also supported a data analyst who was building dashboards by writing SQL queries and explaining the warehouse service's schema.

**Undergraduate Intern, ValueChain Analytics** | Remote | June 2023 – July 2023

During my final undergraduate summer, I interned at ValueChain Analytics, a small firm providing supply chain visibility software to mid-market retailers. I wrote Python scripts to ingest order data from a client's e-commerce system via their API and transform it into a standardized format for analysis. I also helped build a simple web dashboard using Flask and PostgreSQL to let the client visualize their own order trends and fulfillment metrics. The work was scoped and handed to me with clear requirements; I executed the implementation without much oversight, but it wasn't a critical system—it was an internal reporting tool. I gained exposure to end-to-end feature delivery and learned how to think about data pipelines and API design from a user's perspective.

## Education

**Bachelor of Science in Computer Science** | University of Pittsburgh | May 2023

## Technical Skills

Python, JavaScript, SQL, PostgreSQL, Redis, REST APIs, Flask, AWS (EC2, RDS, S3), Docker, Git, LLM APIs (basic prompt engineering), Git, Postman
