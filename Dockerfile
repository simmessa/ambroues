FROM python:3.8 AS build-env
COPY ambroues.py /app/ambroues.py
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install -r requirements.txt

from python:3.8-alpine
COPY --from=build-env /app /app
COPY --from=build-env /opt/venv /opt/venv
WORKDIR /app
ENV VIRTUAL_ENV /app/env
ENV PATH="/opt/venv/bin:$PATH"
CMD ["python","ambroues.py"]