#!/bin/bash
#
# Test TCPDBench build using Docker
#
# Author: G.J.J. van den Burg
# Date: 2021-01-26
#

set -e -u -x -o pipefail

echo "Building docker image"

docker build -t alan-turing-institute/tcpdbench .

echo "Creating output directory"

mkdir -p ${GITHUB_WORKSPACE}/analysis/output

echo "Recreating results and checking for differences"

docker run -v ${GITHUB_WORKSPACE}/analysis/output:/TCPDBench/analysis/output \
	alan-turing-institute/tcpdbench \
	/bin/bash -c "make clean && make results && git checkout ./analysis/output/rankplots/*.pdf && git diff --exit-code"

echo "Test building the virtual environments"

docker run alan-turing-institute/tcpdbench /bin/bash -c "make venvs"
