FROM python:3.11-slim

WORKDIR /app

# The AI modules are mounted at /app/ai and imported as top-level packages
# (task_allocation, path_planning, fsm, obstacle_awareness).
ENV PYTHONPATH=/app/ai

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
