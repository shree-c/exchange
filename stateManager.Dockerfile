FROM python:3.9.19-slim-bullseye

RUN apt-get update && apt-get upgrade -y

WORKDIR /app

COPY /algotest_assignment/state-manager/requirement.txt /app/requirement.txt
RUN pip install -r requirement.txt
ADD /algotest_assignment/crud /app/crud
RUN pip install -e ./crud
COPY /algotest_assignment/state-manager /app
RUN pip install -e .

CMD ["python", "-m", "sm"]
