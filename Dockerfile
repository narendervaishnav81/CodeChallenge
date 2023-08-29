# Step 1 select default OS image
FROM python:3.10-slim-bullseye
 
# # Step 2 tell what you want to do
RUN apt-get update -y && apt-get install -y python3-pip
 
# # Step 3 Configure a software
# # Defining working directory
WORKDIR /app

# # Copy everything which is present in my docker directory to working (/app)
COPY /requirements.txt /app

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt


COPY ["crud_mongo.py", "/app"]

# Exposing an internal port
EXPOSE 5001


# Step 4 set default commands
# These are permanent commands i.e even if user will provide come commands those will be considered as argunemts of this command
ENTRYPOINT [ "python3" ]

# These commands will be replaced if user provides any command by himself
CMD ["crud_mongo.py"]
