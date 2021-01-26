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

mkdir -p ${GITHUB_WORKSPACE}/analysis/output

docker run -v ${GITHUB_WORKSPACE}/analysis/output:/TCPDBench/analysis/output \
	alan-turing-institute/tcpdbench \
	/bin/bash -c "make clean && make results && git checkout ./analysis/output/rankplots/*.pdf && git diff --exit-code"
