# Makefile for CPDBench
#
# Author: G.J.J. van den Burg
# Copyright (c) 2019, The Alan Turing Institute
# License: MIT
# Date: 2019-10-02
#

SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables --no-builtin-rules

DATA_DIR=./datasets
OUTPUT_DIR=./analysis/output
TABLE_DIR=$(OUTPUT_DIR)/tables
RANK_DIR=$(OUTPUT_DIR)/rankplots
CONST_DIR=$(OUTPUT_DIR)/constants
SCRIPT_DIR=./analysis/scripts

SUMMARY_DIR=$(OUTPUT_DIR)/summaries
RESULT_DIR=./abed_results

ANNOTATION_FILE=./analysis/annotations/annotations.json

DATASETS=$(sort $(filter-out demo_*, $(wildcard $(DATA_DIR)/*.json)))
DATANAMES=$(subst $(DATA_DIR)/,,$(subst .json,,$(DATASETS)))
DATASET_SUMMARIES=$(addsuffix .json,$(addprefix $(SUMMARY_DIR)/summary_,$(DATANAMES)))

#############
#           #
# Top-level #
#           #
#############

.PHONY: all clean

all: results

results: tables rankplots constants

#############
#           #
# Summaries #
#           #
#############

.PHONY: summary-dir summaries

summary-dir:
	mkdir -p $(SUMMARY_DIR)

summaries: $(DATASET_SUMMARIES)

$(DATASET_SUMMARIES): $(SUMMARY_DIR)/summary_%.json: $(DATA_DIR)/%.json $(SCRIPT_DIR)/summarize.py | summary-dir
	python $(SCRIPT_DIR)/summarize.py -a $(ANNOTATION_FILE) -d $< -r $(RESULT_DIR) -o $@

clean_summaries:
	rm -f $(DATASET_SUMMARIES)

##########
#        #
# Tables #
#        #
##########

.PHONY: tables default_tables best_tables aggregate_wide

tables: default_tables best_tables aggregate_wide

best_tables: \
	$(TABLE_DIR)/best_f1_combined_full.tex \
	$(TABLE_DIR)/best_cover_combined_full.tex \
	$(TABLE_DIR)/best_f1_uni_avg.json \
	$(TABLE_DIR)/best_f1_multi_avg.json \
	$(TABLE_DIR)/best_cover_uni_avg.json \
	$(TABLE_DIR)/best_cover_multi_avg.json \
	$(TABLE_DIR)/best_f1_uni_full.json \
	$(TABLE_DIR)/best_cover_uni_full.json

$(TABLE_DIR)/best_f1_combined_full.tex: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e best -m f1 -d combined -f tex -t full > $@

$(TABLE_DIR)/best_cover_combined_full.tex: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e best -m cover -d combined -f tex -t full > $@

$(TABLE_DIR)/best_f1_uni_avg.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e best -m f1 -d uni -f json -t avg > $@

$(TABLE_DIR)/best_f1_multi_avg.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e best -m f1 -d multi -f json -t avg > $@

$(TABLE_DIR)/best_cover_uni_avg.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e best -m cover -d uni -f json -t avg > $@

$(TABLE_DIR)/best_cover_multi_avg.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e best -m cover -d multi -f json -t avg > $@

$(TABLE_DIR)/best_cover_uni_full.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e best -m cover -d uni -f json -t full > $@

$(TABLE_DIR)/best_f1_uni_full.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e best -m f1 -d uni -f json -t full > $@

default_tables: \
	$(TABLE_DIR)/default_f1_combined_full.tex \
	$(TABLE_DIR)/default_cover_combined_full.tex \
	$(TABLE_DIR)/default_f1_uni_avg.json \
	$(TABLE_DIR)/default_f1_multi_avg.json \
	$(TABLE_DIR)/default_cover_uni_avg.json \
	$(TABLE_DIR)/default_cover_multi_avg.json \
	$(TABLE_DIR)/default_cover_uni_full.json \
	$(TABLE_DIR)/default_f1_uni_full.json

$(TABLE_DIR)/default_f1_combined_full.tex: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e default -m f1 -d combined -f tex -t full > $@

$(TABLE_DIR)/default_cover_combined_full.tex: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e default -m cover -d combined -f tex -t full > $@

$(TABLE_DIR)/default_f1_uni_avg.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e default -m f1 -d uni -f json -t avg > $@

$(TABLE_DIR)/default_f1_multi_avg.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e default -m f1 -d multi -f json -t avg > $@

$(TABLE_DIR)/default_cover_uni_avg.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e default -m cover -d uni -f json -t avg > $@

$(TABLE_DIR)/default_cover_multi_avg.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e default -m cover -d multi -f json -t avg > $@

$(TABLE_DIR)/default_cover_uni_full.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e default -m cover -d uni -f json -t full > $@

$(TABLE_DIR)/default_f1_uni_full.json: $(SCRIPT_DIR)/make_table.py summaries
	python $< -s $(SUMMARY_DIR) -e default -m f1 -d uni -f json -t full > $@


aggregate_wide: $(TABLE_DIR)/aggregate_table_wide.tex

$(TABLE_DIR)/aggregate_table_wide.tex: $(SCRIPT_DIR)/aggregate_table_wide.py \
	$(TABLE_DIR)/best_cover_uni_avg.json \
	$(TABLE_DIR)/best_cover_multi_avg.json \
	$(TABLE_DIR)/best_f1_uni_avg.json \
	$(TABLE_DIR)/best_f1_uni_avg.json \
	$(TABLE_DIR)/default_cover_uni_avg.json \
	$(TABLE_DIR)/default_cover_multi_avg.json \
	$(TABLE_DIR)/default_f1_uni_avg.json \
	$(TABLE_DIR)/default_f1_uni_avg.json
	python $< \
		--bcu $(TABLE_DIR)/best_cover_uni_avg.json \
		--bcm $(TABLE_DIR)/best_cover_multi_avg.json \
		--bfu $(TABLE_DIR)/best_f1_uni_avg.json \
		--bfm $(TABLE_DIR)/best_f1_multi_avg.json \
		--dcu $(TABLE_DIR)/default_cover_uni_avg.json \
		--dcm $(TABLE_DIR)/default_cover_multi_avg.json \
		--dfu $(TABLE_DIR)/default_f1_uni_avg.json \
		--dfm $(TABLE_DIR)/default_f1_multi_avg.json > $@


clean_tables:
	rm -f $(TABLE_DIR)/aggregate_table.tex
	rm -f $(TABLE_DIR)/best_cover_combined_full.tex
	rm -f $(TABLE_DIR)/best_cover_multi_avg.json
	rm -f $(TABLE_DIR)/best_cover_uni_avg.json
	rm -f $(TABLE_DIR)/best_cover_uni_full.js
	rm -f $(TABLE_DIR)/best_f1_combined_full.tex
	rm -f $(TABLE_DIR)/best_f1_multi_avg.json
	rm -f $(TABLE_DIR)/best_f1_uni_avg.json
	rm -f $(TABLE_DIR)/best_f1_uni_full.json
	rm -f $(TABLE_DIR)/default_cover_combined_full.tex
	rm -f $(TABLE_DIR)/default_cover_multi_avg.json
	rm -f $(TABLE_DIR)/default_cover_uni_avg.json
	rm -f $(TABLE_DIR)/default_cover_uni_full.json
	rm -f $(TABLE_DIR)/default_f1_combined_full.tex
	rm -f $(TABLE_DIR)/default_f1_multi_avg.json
	rm -f $(TABLE_DIR)/default_f1_uni_avg.json
	rm -f $(TABLE_DIR)/default_f1_uni_full.json


##############
#            #
# Rank plots #
#            #
##############

.PHONY: rankplots

rankplots: \
	$(RANK_DIR)/rankplot_best_cover_uni.tex \
	$(RANK_DIR)/rankplot_best_f1_uni.tex \
	$(RANK_DIR)/rankplot_default_cover_uni.tex \
	$(RANK_DIR)/rankplot_default_f1_uni.tex \
	$(RANK_DIR)/rankplot_best_cover_uni.pdf \
	$(RANK_DIR)/rankplot_best_f1_uni.pdf \
	$(RANK_DIR)/rankplot_default_cover_uni.pdf \
	$(RANK_DIR)/rankplot_default_f1_uni.pdf

$(RANK_DIR)/rankplot_best_cover_uni.tex: $(TABLE_DIR)/best_cover_uni_full.json $(SCRIPT_DIR)/rank_plots.py
	python $(SCRIPT_DIR)/rank_plots.py -i $< -o $@ -b max --type best

$(RANK_DIR)/rankplot_best_f1_uni.tex: $(TABLE_DIR)/best_f1_uni_full.json $(SCRIPT_DIR)/rank_plots.py
	python $(SCRIPT_DIR)/rank_plots.py -i $< -o $@ -b max --type best

$(RANK_DIR)/rankplot_default_cover_uni.tex: $(TABLE_DIR)/default_cover_uni_full.json $(SCRIPT_DIR)/rank_plots.py
	python $(SCRIPT_DIR)/rank_plots.py -i $< -o $@ -b max --type default

$(RANK_DIR)/rankplot_default_f1_uni.tex: $(TABLE_DIR)/default_f1_uni_full.json $(SCRIPT_DIR)/rank_plots.py
	python $(SCRIPT_DIR)/rank_plots.py -i $< -o $@ -b max --type default

$(RANK_DIR)/rankplot_%.pdf: $(RANK_DIR)/rankplot_%.tex
	latexmk -pdf -pdflatex="pdflatex -interaction=nonstopmode --shell-escape" \
		-outdir=$(RANK_DIR) $<
	cd $(RANK_DIR) && latexmk -c

clean_rankplots:
	rm -f $(RANK_DIR)/rankplot_best_cover_uni.tex
	rm -f $(RANK_DIR)/rankplot_best_f1_uni.tex
	rm -f $(RANK_DIR)/rankplot_default_cover_uni.tex
	rm -f $(RANK_DIR)/rankplot_default_f1_uni.tex


###############
#             #
#  Constants  #
#             #
###############

.PHONY: constants

CONSTANT_TARGETS = \
		   $(CONST_DIR)/sigtest_global_best_cover_uni.tex \
		   $(CONST_DIR)/sigtest_global_best_f1_uni.tex \
		   $(CONST_DIR)/sigtest_global_default_cover_uni.tex \
		   $(CONST_DIR)/sigtest_global_default_f1_uni.tex

constants: $(CONSTANT_TARGETS)

$(CONST_DIR)/sigtest_global_best_cover_uni.tex: $(TABLE_DIR)/best_cover_uni_full.json \
	$(SCRIPT_DIR)/significance.py
	python $(SCRIPT_DIR)/significance.py -i $< -o $@ --type best --mode global

$(CONST_DIR)/sigtest_global_best_f1_uni.tex: $(TABLE_DIR)/best_f1_uni_full.json \
	$(SCRIPT_DIR)/significance.py
	python $(SCRIPT_DIR)/significance.py -i $< -o $@ --type best --mode global

$(CONST_DIR)/sigtest_global_default_cover_uni.tex: $(TABLE_DIR)/default_cover_uni_full.json \
	$(SCRIPT_DIR)/significance.py
	python $(SCRIPT_DIR)/significance.py -i $< -o $@ --type best --mode global

$(CONST_DIR)/sigtest_global_default_f1_uni.tex: $(TABLE_DIR)/default_f1_uni_full.json \
	$(SCRIPT_DIR)/significance.py
	python $(SCRIPT_DIR)/significance.py -i $< -o $@ --type best --mode global

clean_constants:
	rm -f $(CONSTANT_TARGETS)

###############
#             #
# Virtualenvs #
#             #
###############

.PHONY: venv_bocpdms venv_rbocpdms R_venv venvs

venvs: venv_bocpdms venv_rbocpdms R_venv

venv_bocpdms: ./execs/python/bocpdms/venv

./execs/python/bocpdms/venv:
	cd execs/python/bocpdms && virtualenv venv && source venv/bin/activate && pip install -r requirements.txt

venv_rbocpdms: ./execs/python/rbocpdms/venv

./execs/python/rbocpdms/venv:
	cd execs/python/rbocpdms && virtualenv venv && source venv/bin/activate && pip install -r requirements.txt

R_venv:
	bash ./utils/R_setup.sh Rpackages.txt ./execs/R/rlibs

clean_R_venv:
	rm -rf ./execs/R/rlibs
	rm -f ./.Rprofile ./.Renviron
	rm -f ./.Renviron

clean_venvs: clean_R_venv
	rm -rf ./execs/python/bocpdms/venv
	rm -rf ./execs/python/rbocpdms/venv

##############
#            #
# Validation #
#            #
##############

.PHONY: validate

validate: ./utils/validate_schema.py ./schema.json
	python $< -s ./schema.json -r $(RESULT_DIR)

###########
#         #
# Cleanup #
#         #
###########

clean: clean_summaries clean_tables clean_rankplots clean_venvs
