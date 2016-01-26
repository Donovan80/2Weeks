############################################################
# Dockerfile to build 2weeks App
FROM python:2-onbuild

#Move files

COPY /. /usr/src/app

WORKDIR /usr/src/app

CMD [ "python", "/usr/src/app/app.py" ]

#git clone https://github.com/Donovan80/App.git