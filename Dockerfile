from python:3.8-alpine

COPY ambroues.py /app/ambroues.py
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["ambroues.py"]