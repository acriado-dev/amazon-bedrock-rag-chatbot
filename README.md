# amazon-bedrock-rag-chatbot
Streamlit RAG Chatbot by using Amazon bedrock converse API 



## Python

- create the ".venv" environment:

```
python3 -m venv .venv
```

- Activate virtual environment
```
source .venv/bin/activate
```
- Upgrade pip (recommended)
```
python3 -m pip install --upgrade pip
```

- Install required packages
```
pip install chromadb
```

- Deactivate virtual environment
```
deactivate
```

## Streamlit

- Go to `./chatbot/` folder

- You can run streamlit locally with the following 2 commands:

```
python -m streamlit run streamlit_hello_world.py
streamlit run rag_chatbot_app.py --server.port 8080
```

## Docker

- Build:
```
sudo docker build -t rag-chatbot:develop.1 .
```

- Run:
```
docker run -e AWS_ACCESS_KEY_ID=XXXXXXXXXX \
           -e AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXx \
           -e AWS_DEFAULT_REGION=eu-central-1 \
           rag-chatbot:develop.1
```


