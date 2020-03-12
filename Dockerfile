FROM ubuntu:19.04

RUN apt-get update && \
	DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && \
	apt-get remove -y python && \
	apt-get install -y --no-install-recommends \
		git \
		build-essential \
		r-base \
		latexmk \
		libopenmpi-dev \
		liblzma-dev

# Make sure python means python3
RUN apt-get install -y --no-install-recommends \
	python3 \
	python3-dev \
	python3-pip && \
    pip3 install --no-cache-dir --upgrade pip setuptools && \
	echo "alias python='python3'" >> /root/.bash_aliases && \
	echo "alias pip='pip3'" >> /root/.bash_aliases && \
	cd /usr/local/bin && ln -s /usr/bin/python3 python && \
    pip install virtualenv abed

# Clone the dataset repo
RUN git clone https://github.com/alan-turing-institute/TCPD

# Build the dataset
RUN cd TCPD && make export

# Clone the repo
RUN git clone --recurse-submodules https://github.com/alan-turing-institute/TCPDBench

# Copy the datasets into the benchmark dir
RUN mkdir -p TCPDBench/datasets && cp TCPD/export/*.json TCPDBench/dataset/

# Set the working directory
WORKDIR TCPDBench
