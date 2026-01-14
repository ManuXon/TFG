# MapAI-UB (TFG) — Visual Analytics + Gated Chatbot

Web-based visual analytics platform to explore survey data about AI tool usage in teaching at the University of Barcelona (UB).  
The system combines interactive dashboards (quantitative aggregates + coordinated filtering) with qualitative open-text exploration (sentiment/topic groupings) and a gated chatbot for computation-grounded Q&A.

> **Note:** The `dev` branch contains the latest changes.

---

## Run the platform (production compose)

From the repository root:

```bash
docker-compose -f docker-compose.prod.yml up
