\# AIOpsGenie — AI-Powered IT Operations \& Incident Management Platform



AIOpsGenie is a locally hosted AI-powered IT operations assistant built with Python, Flask, LangGraph, Ollama, FAISS, and SQLite.



It combines AI-assisted IT support, knowledge-base retrieval, ticket management, system-resource monitoring, alert generation, and incident lifecycle management in a unified web dashboard.



The project demonstrates how AI, retrieval-augmented generation (RAG), workflow orchestration, and system monitoring can support common IT operations workflows.



\## Key Features



\### 1. AI-Powered IT Support Assistant

\- Processes user requests through a LangGraph workflow.

\- Classifies requests into support, knowledge, general, ticket, and system-monitoring categories.

\- Uses a locally hosted Llama 3.2 model through Ollama.

\- Provides responses grounded in retrieved knowledge when handling support and knowledge queries.



\### 2. Retrieval-Augmented Generation (RAG)

\- Uses FAISS for vector-based knowledge retrieval.

\- Uses Sentence Transformers for text embeddings.

\- Retrieves relevant knowledge-base content for user queries.

\- Generates answers using retrieved context.

\- Provides a fallback when relevant information is unavailable.



\### 3. IT Ticket Management

\- Creates support tickets through the AI assistant.

\- Retrieves ticket details and status.

\- Stores ticket information in SQLite.

\- Supports ticket priorities and lifecycle tracking.



\### 4. System Resource Monitoring

\- Collects actual local system metrics using `psutil`.

\- Monitors CPU utilization.

\- Monitors RAM utilization.

\- Monitors disk utilization.

\- Calculates overall system health.



\### 5. System Alerts

\- Generates alerts when resource utilization crosses configured thresholds.

\- Supports warning and critical severity levels.

\- Maintains alert history.

\- Resolves alerts when monitored metrics return below warning thresholds.



\### 6. Incident Management

\- Automatically creates critical incident tickets from qualifying system alerts.

\- Prevents duplicate alert-linked tickets.

\- Supports incident assignment.

\- Supports acknowledgment and resolution.

\- Maintains incident notes and resolution summaries.

\- Synchronizes qualifying resolved alerts with their linked incident tickets.



\### 7. Flask Web Dashboard

\- System overview and ticket statistics.

\- CPU, RAM, and disk monitoring.

\- Resource usage history charts.

\- Active and historical system alerts.

\- Incident management queue.

\- Ticket history.

\- AI support assistant.

\- Service monitoring overview.



\*\*Monitoring note:\*\* CPU, RAM, and disk metrics are collected from the local machine. VPN, email, database, firewall, and web service statuses are currently simulated demonstration data, not live external service health checks.



\## Technology Stack



| Component | Technology |

|---|---|

| Backend | Python |

| Web Framework | Flask |

| AI Model | Llama 3.2:3b |

| Local Model Runtime | Ollama |

| Workflow Orchestration | LangGraph |

| LLM Integration | LangChain |

| RAG | Retrieval-Augmented Generation |

| Vector Database | FAISS |

| Embeddings | Sentence Transformers |

| Database | SQLite |

| System Monitoring | psutil |

| Frontend | HTML, CSS, JavaScript |

| Charts | Chart.js |



\## Architecture



```mermaid

flowchart TD

&#x20;   A\[User] --> B\[Flask Web Dashboard]

&#x20;   B --> C\[LangGraph Workflow]

&#x20;   C --> D\[Request Classification]



&#x20;   D --> E\[Ticket Management]

&#x20;   D --> F\[System Monitoring]

&#x20;   D --> G\[Knowledge Retrieval]

&#x20;   D --> H\[General AI Response]



&#x20;   G --> I\[FAISS Vector Store]

&#x20;   I --> J\[Retrieved Knowledge]

&#x20;   J --> K\[Ollama Llama 3.2]



&#x20;   H --> K



&#x20;   E --> L\[SQLite Database]

&#x20;   F --> M\[psutil System Metrics]

&#x20;   M --> N\[System Alerts]

&#x20;   N --> O\[Incident Synchronization]

&#x20;   O --> L



&#x20;   L --> B

&#x20;   K --> B

```



\## Project Structure



```text

AIOPS\_GENIE/

│

├── app/

│   ├── \_\_init\_\_.py

│   ├── run.py

│   ├── routes.py

│   │

│   ├── agents/

│   │   ├── graph.py

│   │   └── state.py

│   │

│   ├── rag/

│   │   ├── loader.py

│   │   ├── embeddings.py

│   │   └── retriever.py

│   │

│   ├── tools/

│   │   ├── ticket\_tool.py

│   │   └── system\_tool.py

│   │

│   └── database/

│       └── db.py

│

├── data/

│   ├── knowledge/

│   ├── vectorstore/

│   └── aiopsgenie.db

│

├── logs/

├── reports/

├── static/

│   ├── style.css

│   └── app.js

│

├── templates/

│   └── index.html

│

├── tests/

│   ├── run\_evaluation.py

│   ├── test\_evaluation.py

│   ├── test\_graph.py

│   ├── test\_incident\_lifecycle.py

│   ├── test\_rag.py

│   ├── test\_system\_api.py

│   ├── test\_system\_monitoring.py

│   └── test\_tools.py

│

├── requirements.txt

└── README.md

```



\## Installation and Setup



\### Prerequisites



\- Python 3.10 or later.

\- Git.

\- Ollama.

\- Sufficient RAM and disk space for the local language model and embedding model.



\### 1. Clone the Repository



```bash

git clone https://github.com/YOUR\_USERNAME/AIOpsGenie.git

cd AIOpsGenie

```



Replace `YOUR\_USERNAME` with your GitHub username.



\### 2. Create a Virtual Environment



Windows:



```powershell

python -m venv .venv

.venv\\Scripts\\Activate.ps1

```



Linux/macOS:



```bash

python3 -m venv .venv

source .venv/bin/activate

```



\### 3. Install Dependencies



```bash

python -m pip install --upgrade pip

pip install -r requirements.txt

```



\### 4. Install and Start Ollama



Install Ollama, then download the model:



```bash

ollama pull llama3.2:3b

```



Ensure the Ollama service is running before starting the application.



\### 5. Initialize the Database



```bash

python -m app.database.db

```



\### 6. Start AIOpsGenie



```bash

python -m app.run

```



Open the dashboard:



```text

http://127.0.0.1:5000

```



\## Running Tests



Run the evaluation tests:



```bash

python -m tests.test\_evaluation

```



Run system monitoring tests:



```bash

python -m tests.test\_system\_monitoring

```



Run system API tests:



```bash

python -m tests.test\_system\_api

```



Run incident lifecycle integration tests:



```bash

python -m tests.test\_incident\_lifecycle

```



Run the evaluation script:



```bash

python -m tests.run\_evaluation

```



Tests should be run with the project's virtual environment activated.



\## Incident Lifecycle



AIOpsGenie supports an alert-to-incident workflow:



1\. System metrics are collected.

2\. Configured thresholds are evaluated.

3\. Qualifying alerts are created.

4\. Critical alerts can generate linked incident tickets.

5\. Duplicate alert-linked tickets are prevented.

6\. Incidents can be assigned and acknowledged.

7\. Incidents can be resolved with resolution summaries.

8\. Resolved alerts can synchronize their status with linked incidents.



\## Current Project Scope



AIOpsGenie is a local development and demonstration project.



\- AI responses use a locally hosted Ollama model.

\- Request routing combines explicit rule-based checks with LLM-based classification.

\- Knowledge retrieval uses a local FAISS vector store.

\- System resource metrics come from the machine running the application.

\- The listed service-status checks are simulated.

\- The application is not yet configured as a production deployment.



\## Future Enhancements



\- Real service health checks and integrations.

\- Authentication and role-based access control.

\- Additional monitoring integrations.

\- More configurable alert rules.

\- Enhanced incident reporting and analytics.

\- Deployment using Docker.

\- Production-ready logging and configuration.

\- Additional knowledge-base documents and evaluation datasets.



\## Author



\*\*Sankar Kharada\*\*



B.Tech Computer Science and Engineering — Cybersecurity



GitHub: https://github.com/Sankarkharada



LinkedIn: https://www.linkedin.com/in/sankar-kharada-83895b2a8/

