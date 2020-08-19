FROM ubuntu:20.04

RUN apt-get update && \
	DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata && \
	apt-get remove -y python && \
	apt-get install -y --no-install-recommends \
		git \
		build-essential \
		r-base \
		r-base-dev \
		latexmk \
		texlive-latex-extra \
		libopenmpi-dev \
		liblzma-dev \
		libgit2-dev \
		libxml2-dev \
		libcurl4-openssl-dev \
		libssl-dev \
		libopenblas-dev \
		libfreetype6-dev \
		libv8-dev

RUN apt-get install -y --no-install-recommends \
	r-cran-askpass r-cran-assertthat r-cran-backports r-cran-base64enc \
	r-cran-bh r-cran-brew r-cran-callr r-cran-checkmate r-cran-cli \
	r-cran-cliapp r-cran-clipr r-cran-clisymbols r-cran-colorspace \
	r-cran-commonmark r-cran-covr r-cran-crayon r-cran-crosstalk \
	r-cran-curl r-cran-desc r-cran-digest r-cran-dplyr r-cran-dt \
	r-cran-dygraphs r-cran-ellipsis r-cran-evaluate r-cran-extradistr \
	r-cran-fansi r-cran-farver r-cran-fs r-cran-ggplot2 r-cran-gh \
	r-cran-git2r r-cran-glue r-cran-gridextra r-cran-gtable r-cran-highr \
	r-cran-htmltools r-cran-htmlwidgets r-cran-httr r-cran-ini \
	r-cran-inline r-cran-jsonlite r-cran-knitr r-cran-labeling \
	r-cran-later r-cran-lazyeval r-cran-lifecycle r-cran-loo \
	r-cran-magrittr r-cran-markdown r-cran-matrixstats r-cran-memoise \
	r-cran-mime r-cran-munsell r-cran-openssl r-cran-pillar \
	r-cran-pkgbuild r-cran-pkgconfig r-cran-pkgload r-cran-praise \
	r-cran-prettyunits r-cran-processx r-cran-promises r-cran-ps \
	r-cran-pscbs r-cran-pscl r-cran-psy r-cran-psych r-cran-psychometric \
	r-cran-psychotools r-cran-psychotree r-cran-psychtools r-cran-psyphy \
	r-cran-purrr r-cran-purrrlyr r-cran-r6 r-cran-rcmdcheck \
	r-cran-rcolorbrewer r-cran-rcppparallel r-cran-remotes r-cran-rex \
	r-cran-rlang r-cran-roxygen2 r-cran-rprojroot r-cran-rstan \
	r-cran-rstanarm r-cran-rstantools r-cran-rstudioapi r-cran-rversions \
	r-cran-scales r-cran-sessioninfo r-cran-stanheaders r-cran-stringi \
	r-cran-stringr r-cran-sys r-cran-systemfit r-cran-systemfonts \
	r-cran-testthat r-cran-tibble r-cran-tidyr r-cran-tidyselect \
	r-cran-usethis r-cran-utf8 r-cran-v8 r-cran-vctrs r-cran-viridislite \
	r-cran-whisker r-cran-withr r-cran-xfun r-cran-xml2 r-cran-xopen \
	r-cran-xts r-cran-yaml r-cran-rcppeigen

# Make sure python means python3
RUN apt-get install -y --no-install-recommends \
	python3 \
	python3-dev \
	python3-tk \
	python3-pip && \
    pip3 install --no-cache-dir --upgrade setuptools && \
	echo "alias python='python3'" >> /root/.bash_aliases && \
	echo "alias pip='pip3'" >> /root/.bash_aliases && \
	cd /usr/local/bin && ln -s /usr/bin/python3 python && \
	cd /usr/local/bin && ln -s /usr/bin/pip3 pip && \
    pip install virtualenv abed

# Set the default shell to bash
RUN mv /bin/sh /bin/sh.old && cp /bin/bash /bin/sh

# Clone the dataset repo
RUN git clone https://github.com/alan-turing-institute/TCPD

# Build the dataset
RUN cd TCPD && make export

# Clone the repo
RUN git clone --recurse-submodules https://github.com/alan-turing-institute/TCPDBench

# Copy the datasets into the benchmark dir
RUN mkdir -p /TCPDBench/datasets && cp TCPD/export/*.json /TCPDBench/datasets/

# Install Python dependencies
RUN pip install -r /TCPDBench/analysis/requirements.txt

# Set the working directory
WORKDIR TCPDBench
