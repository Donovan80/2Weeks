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



# Install / Update
RUN apt-get update && apt-get install -y \
    git \
    python \
    python-dev \
    python-setuptools \
    build-essential \
    nginx \
    supervisor \
    mysql-client \
    install \
    software-properties-common \
    python-software-properties \
    python-pip


# Install uwsgi now because it takes a little while
RUN pip install uwsgi

# Nginx Repo
RUN add-apt-repository ppa:nginx/stable

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


# Expose ports
EXPOSE 80
CMD ["supervisord", "-n"]
