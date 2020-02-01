FROM python:3.8-buster
COPY ./frontend/dist /app/frontend/dist
COPY ./local /app/local
COPY ./*.py /app/
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN mkdir -p /app/relmons
VOLUME /app/relmons
RUN pip install -r requirements.txt
EXPOSE 8002/tcp
CMD python3 /app/main.py --mode env
