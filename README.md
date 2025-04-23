# multi-ai-agent-ecommerce

### Running the app locally:

1. Create python virtual environment

```bash
python -m venv venv
```

2. Activate python virtual environment
```bash
source venv/bin/activate      # mac
source venv/Scripts/activate  # windows
```

3. Install requirements
```bash
pip install -r requirements.txt
```

4. Set environment variables
- create `.env` file in the root project directory
- set the environment variables like in `.env-template`

5. Run mistral LLM locally with oLlama. If you don't have ollama on your machine, download from https://ollama.com/download, install ollama and then run:
```bash
ollama run mistral
```

6. Run CLI app
```bash
python main.py
```
