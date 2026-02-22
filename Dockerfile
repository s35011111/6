
FROM python:3.10
WORKDIR  /myapp
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python","manage.py","runsserver","0.0.0.0:8000"]

