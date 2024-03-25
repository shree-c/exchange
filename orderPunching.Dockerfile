FROM python:3.9.19-slim-bullseye

RUN apt-get update && apt-get upgrade -y

WORKDIR /app

COPY /algotest_assignment/order-punching-interface/requirement.txt /app/requirement.txt
RUN pip install -r requirement.txt
ADD /algotest_assignment/crud /app/crud
RUN pip install -e ./crud
COPY /algotest_assignment/order-punching-interface /app
RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "opi.main:app", "--host", "0.0.0.0", "--port", "8000"]
