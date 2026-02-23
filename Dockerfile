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