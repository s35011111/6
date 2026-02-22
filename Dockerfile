
#FROM python:3.10
#WORKDIR  /myapp
#COPY requirements.txt .
#RUN pip install -r requirements.txt
#COPY . .
#CMD ["python","manage.py","runserver","0.0.0.0:8000"]

# Dockerfile - Universal Python image
FROM python:3.10


# Set work directory
WORKDIR /myapp

# Install system dependencies

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]