FROM python:3.12

RUN pip install --no-cache-dir pipenv --root-user-action=ignore

WORKDIR /var/www/cba-langchain-streamlit

RUN useradd -m -u 1000 streamlituser

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy --ignore-pipfile

COPY . .

RUN chown -R streamlituser:streamlituser /var/www/cba-langchain-streamlit

USER streamlituser

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.runOnSave=true"]
