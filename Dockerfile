############################################################
# Dockerfile to build 2weeks App
# Based on Ubuntu
# This is the Devlopement Build
############################################################
# Set the base image to Ubuntu
FROM ubuntu:wily
# Add the application resources URL
#RUN echo "deb http://apt.dockerproject.org/repo/dists/ubuntu-wily/main" > /etc/apt/sources.list

# File Author / Maintainer
MAINTAINER Robert Donovan <robert.b.donovan@gmail.com>

# Update the sources list and Install basic applications
run perl -p -i.orig -e 's/archive.ubuntu.com/mirrors.aliyun.com\/ubuntu/' /etc/apt/sources.list
RUN apt-get install -y build-essential git
RUN apt-get install -y python python-dev python-setuptools
RUN apt-get install -y nginx supervisor
RUN easy_install pip

# Install uwsgi now because it takes a little while
RUN pip install uwsgi

# Install nginx
RUN apt-get install -y software-properties-common python-software-properties
RUN add-apt-repository ppa:nginx/stable
RUN apt-get install mysql-client

#Install App code
add . /home/docker/code/

#Config files
RUN echo "deamon off;" >> /etc/nginx/nginx.conf
RUN rm /etc/nginx/sites-enabled/default
RUN ln -s /home/docker/code/nginx-app.conf /etc/nginx/site-enabled/
RUN ln -s /home/docker/code/supervisor-app.conf /etc/supervisor/conf.d/

# Copy the application folder inside the container
RUN git clone https://github.com/mixfinancial/2Weeks.git

# Get pip to download and install requirements:
RUN pip install -r /2Weeks/requirements.txt

#Run the setup script from Dave
#RUN chmod +x /2Weeks/scripts/bootstrap.sh

#Rerun the Update to resolve install issues
RUN apt-get update -f

# Expose ports
EXPOSE 80
CMD ["supervisord", "-n"]
