FROM python:3.9-alpine
WORKDIR .
COPY . .
RUN pip install -r requirements.txt
ENV FLASK_ENV development
EXPOSE 5000
ENTRYPOINT ["python"]
CMD ["python","app.py"]