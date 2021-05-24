# set base image (host OS)
FROM python:3.9

# set the working directory in the container
WORKDIR /blackjack

# copy the dependencies file to the working directory
#COPY requirements.txt .

# install dependencies
#RUN pip install -r requirements.txt

# copy the content of the local directory to the working directory
COPY blackjack/* ./

COPY config-example.py ./core/config.py

# command to run on container start
CMD [ "python", "-u", "./blackjack.py" ]