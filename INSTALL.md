Basic installation steps
========================

Dependencies
------------

-   pip
-   pip3
-   cmake

1. Dockerlaunch
---------------

To install:

    sudo apt-get install docker.io
    sudo pip3 install lockfile
    sudo pip3 install git+git://github.com/numa-engineering/python-daemon.git@master
    sudo pip3 install docker-py
    git clone https://github.com/go-smart/dockerlaunch.git

    cd dockerlaunch
    cmake .
    make
    sudo make install
    cd ..

To run:

    sudo dockerlaunchd start

2. Glossia
----------

To install:

    sudo pip install docker-compose
    sudo docker pull gosmart/glossia
    git clone https://github.com/go-smart/glossia-server-side.git
    cd glossia-server-side
    sudo ./setup.sh

To add simulation families (sandbox images):

    sudo docker pull gosmart/glossia-goosefoot
    sudo docker pull gosmart/glossia-fenics

To run (from `glossia-server-side`):

    export COMPOSE_API_VERSION=$(sudo docker version | grep 'Server API' | awk '{ print $NF }')
    sudo COMPOSE_API_VERSION="$COMPOSE_API_VERSION" docker-compose up

(if your docker-compose API version matches your docker version, then
`sudo docker-compose up` is sufficient)
