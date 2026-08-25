# Hana Novak
AI/ML Engineer | Healthcare AI | Boston, MA | (617) 842-3156 | hana.novak@mail.com

## Experience

**Senior ML Engineer, BioSignal Systems Inc.** | Boston, MA | March 2024 – Present
- Architected retrieval-augmented generation pipeline for clinical literature synthesis, integrating vector database (Weaviate) with GPT-4 for evidence-based recommendations on rare genetic disorders
- Developed multi-agent framework using LangGraph where specialized agents handle literature retrieval, statistical analysis, and clinical guideline cross-referencing; achieved 94.2% accuracy on internal benchmark dataset of 2,847 curated case studies
- Fine-tuned open-source Llama 2 variant (13B) on 50K+ de-identified patient notes using QLoRA; F1 score improved from 0.71 baseline to 0.89 on held-out eval set of 500 documents
- Built custom evaluation harness with BLEU, ROUGE-L, and domain-specific medical terminology recall metrics; established benchmark suite now used across team for all subsequent model iterations
- Implemented RAG evaluation framework measuring retrieval precision@5 (0.91), semantic similarity of retrieved chunks (cosine similarity 0.84+), and end-to-end latency (<800ms p95)
- Published blog post "Reducing Hallucinations in Medical LLMs Through Structured Retrieval" (1,200 views); presented at Boston ML Meetup on clinical RAG challenges

**ML Engineer, NeuroTrace Analytics** | Cambridge, MA | August 2023 – February 2024
- Developed agentic system for neuroimaging data analysis using ReAct framework; orchestrated agents for image preprocessing, feature extraction, and anomaly detection on brain MRI scans
- Fine-tuned medical BERT variant on 18K clinical notes for named entity recognition (NER) of neurological conditions; achieved 91.3% F1 score across 42 entity types on validation set
- Optimized inference latency for EfficientNet model from 1,200ms to 340ms through quantization and batch processing optimization
- Contributed to open-source medical ML library (185 GitHub stars); maintained documentation and example notebooks for RAG integration with clinical databases

**Data Scientist, Meridian Health Tech** | Providence, RI | June 2023 – July 2023
- Implemented prompt engineering pipeline for generating synthetic clinical vignettes using few-shot examples; evaluated outputs against clinician-authored standards achieving 0.87 semantic similarity
- Developed evaluation datasets for medical language models; curated and annotated 3,000 clinical queries with reference answers and relevant evidence passages
- Experimented with adapter-based fine-tuning methods for rapid domain specialization; benchmarked against full fine-tuning approaches on drug interaction prediction task

**Junior Data Scientist, Pathfinder Diagnostics** | Hartford, CT | January 2023 – May 2023
- Built feature engineering pipeline for diagnostic prediction models; processed raw lab values and vital signs from structured health records
- Collaborated with clinical specialists to define success metrics for phenotyping algorithms; delivered accuracy benchmarks on 1,200-patient cohort
- Created data validation scripts ensuring quality of inputs for downstream ML models

## Technical Skills

**Large Language Models & Agents:** RAG systems, prompt engineering, agentic workflows (LangGraph, ReAct), multi-agent orchestration, instruction fine-tuning, parameter-efficient fine-tuning (LoRA, QLoRA), retrieval optimization

**Models & Frameworks:** GPT-4, Llama 2, Medical BERT, LangChain, Hugging Face Transformers, PyTorch, scikit-learn

**Infrastructure & Tools:** Vector databases (Weaviate, Pinecone), PostgreSQL, Python, FastAPI, Docker, Git, Weights & Biases

**Evaluation & Benchmarking:** BLEU, ROUGE, semantic similarity metrics, custom eval frameworks, held-out test sets, baseline comparisons

## Education

**M.S. Computer Science** | University of Massachusetts, Amherst | 2023 | Thesis: Fine-tuning strategies for low-resource medical NLP

**B.S. Biology with Computer Science Minor** | Northeastern University | 2021

## Publications & Speaking

- "Reducing Hallucinations in Medical LLMs Through Structured Retrieval" — Blog post, August 2024
- "Clinical Applications of Retrieval-Augmented Generation" — Boston ML Meetup talk, June 2024
- Contributor to open-source medical ML library (185★ GitHub)
