FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

EXPOSE 8502

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "rag_chatbot_app.py", "--server.port=8502"]
