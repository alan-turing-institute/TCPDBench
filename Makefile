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
FIGURE_DIR=$(OUTPUT_DIR)/figures
TABLE_DIR=$(OUTPUT_DIR)/tables
SCORE_DIR=$(OUTPUT_DIR)/scores
CDD_DIR=$(OUTPUT_DIR)/cd_diagrams
CONST_DIR=$(OUTPUT_DIR)/constants
SCRIPT_DIR=./analysis/scripts

SUMMARY_DIR=$(OUTPUT_DIR)/summaries
RESULT_DIR=./abed_results

ANNOTATION_FILE=./analysis/annotations/annotations.json

DATASETS=$(sort $(filter-out demo_*, $(wildcard $(DATA_DIR)/*.json)))
DATANAMES=$(subst $(DATA_DIR)/,,$(subst .json,,$(DATASETS)))
DATASET_SUMMARIES=$(addsuffix .json,$(addprefix $(SUMMARY_DIR)/summary_,$(DATANAMES)))

EXPERIMENTS=default oracle
METRICS=cover f1
DIMENSIONALITY=univariate multivariate
MISSING_STRATEGY=zero_no_coal # or 'zero' or 'complete'

#############
#           #
# Top-level #
#           #
#############

.PHONY: all clean results

all: results

results: tables figures cd_diagrams constants

#############
#           #
# Summaries #
#           #
#############

.PHONY: summary-dir summaries

summary-dir:
	mkdir -p $(SUMMARY_DIR)

summaries: $(DATASET_SUMMARIES)

$(DATASET_SUMMARIES): $(SUMMARY_DIR)/summary_%.json: $(DATA_DIR)/%.json \
	$(SCRIPT_DIR)/summarize.py $(SCRIPT_DIR)/metrics.py | summary-dir
	python $(SCRIPT_DIR)/summarize.py -a $(ANNOTATION_FILE) -d $< \
		-r $(RESULT_DIR) -o $@

clean_summaries:
	rm -f $(DATASET_SUMMARIES)

##########
#        #
# Tables #
#        #
##########

.PHONY: tables \
	default_tables \
	oracle_tables \
	aggregate_wide \
	descriptive \
	annotator_agreement

table-dir:
	mkdir -p $(TABLE_DIR)

tables: default_tables \
	oracle_tables \
	aggregate_wide \
	descriptive \
	annotator_agreement

oracle_tables: \
	$(TABLE_DIR)/oracle_f1_combined_full.tex \
	$(TABLE_DIR)/oracle_cover_combined_full.tex

default_tables: \
	$(TABLE_DIR)/default_f1_combined_full.tex \
	$(TABLE_DIR)/default_cover_combined_full.tex

$(TABLE_DIR)/oracle_f1_combined_full.tex: $(SCRIPT_DIR)/make_table.py \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/latex.py \
	$(SCRIPT_DIR)/score_file.py $(DATASET_SUMMARIES) | table-dir
	python $< -s $(SUMMARY_DIR) -e oracle -m f1 > $@

$(TABLE_DIR)/oracle_cover_combined_full.tex: $(SCRIPT_DIR)/make_table.py \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/latex.py \
	$(SCRIPT_DIR)/score_file.py $(DATASET_SUMMARIES) | table-dir
	python $< -s $(SUMMARY_DIR) -e oracle -m cover > $@

$(TABLE_DIR)/default_f1_combined_full.tex: $(SCRIPT_DIR)/make_table.py \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/latex.py \
	$(SCRIPT_DIR)/score_file.py $(DATASET_SUMMARIES) | table-dir
	python $< -s $(SUMMARY_DIR) -e default -m f1 > $@

$(TABLE_DIR)/default_cover_combined_full.tex: $(SCRIPT_DIR)/make_table.py \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/latex.py \
	$(SCRIPT_DIR)/score_file.py $(DATASET_SUMMARIES) | table-dir
	python $< -s $(SUMMARY_DIR) -e default -m cover > $@

aggregate_wide: $(TABLE_DIR)/aggregate_scores_wide.tex

$(TABLE_DIR)/aggregate_scores_wide.tex: $(SCRIPT_DIR)/aggregate_scores_wide.py \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/rank_common.py \
	$(SCRIPT_DIR)/significance.py \
	$(SCORE_DIR)/default_cover_scores.json \
	$(SCORE_DIR)/default_f1_scores.json \
	$(SCORE_DIR)/oracle_cover_scores.json \
	$(SCORE_DIR)/oracle_f1_scores.json | table-dir
	python $< \
		--default-cover $(SCORE_DIR)/default_cover_scores.json \
		--default-f1 $(SCORE_DIR)/default_f1_scores.json \
		--oracle-cover $(SCORE_DIR)/oracle_cover_scores.json \
		--oracle-f1 $(SCORE_DIR)/oracle_f1_scores.json \
		-o $@ -m $(MISSING_STRATEGY)


descriptive: $(TABLE_DIR)/descriptive_statistics.tex

$(TABLE_DIR)/descriptive_statistics.tex: $(SCRIPT_DIR)/descriptive_statistics.py \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/frequencies.py \
	$(DATASET_SUMMARIES) | table-dir
	python $< -d $(DATA_DIR) -s $(SUMMARY_DIR) -o $@

annotator_agreement: $(TABLE_DIR)/annotation_simulation_pvalues.tex

$(TABLE_DIR)/annotation_simulation_pvalues.tex: \
	$(SCRIPT_DIR)/annotator_agreement_simulation.py \
	$(SCRIPT_DIR)/common.py \
	$(SCRIPT_DIR)/latex.py \
	$(SCRIPT_DIR)/metrics.py \
	$(DATASET_SUMMARIES) | table-dir
	python $< -s $(SUMMARY_DIR) -o $@ --seed 123 -r 100000

clean_tables:
	rm -f $(TABLE_DIR)/aggregate_scores_wide.tex
	rm -f $(TABLE_DIR)/default_cover_combined_full.tex
	rm -f $(TABLE_DIR)/default_f1_combined_full.tex
	rm -f $(TABLE_DIR)/oracle_cover_combined_full.tex
	rm -f $(TABLE_DIR)/oracle_f1_combined_full.tex
	rm -f $(TABLE_DIR)/descriptive_statistics.tex
	rm -f $(TABLE_DIR)/annotation_simulation_pvalues.tex

###########
#         #
# Figures #
#         #
###########

.PHONY: figures annotator_histograms clean_figures

figures: annotator_histograms

annotator_histograms: \
	$(FIGURE_DIR)/anno_hist/histogram_f1.pdf \
	$(FIGURE_DIR)/anno_hist/histogram_cover.pdf

figure-dirs:
	mkdir -p $(FIGURE_DIR)
	mkdir -p $(FIGURE_DIR)/anno_hist

$(FIGURE_DIR)/anno_hist/histogram_f1.tex: \
	$(SCRIPT_DIR)/annotator_histogram.py \
	$(SCRIPT_DIR)/common.py \
	$(SCRIPT_DIR)/metrics.py \
	$(DATASET_SUMMARIES) | figure-dirs
	python $< -s $(SUMMARY_DIR) -o $@ --metric f1

$(FIGURE_DIR)/anno_hist/histogram_cover.tex: \
	$(SCRIPT_DIR)/annotator_histogram.py \
	$(SCRIPT_DIR)/common.py \
	$(SCRIPT_DIR)/metrics.py \
	$(DATASET_SUMMARIES) | figure-dirs
	python $< -s $(SUMMARY_DIR) -o $@ --metric covering

$(FIGURE_DIR)/anno_hist/histogram_%.pdf: \
	$(FIGURE_DIR)/anno_hist/histogram_%.tex | figure-dirs
	latexmk -pdf -pdflatex="pdflatex -interaction=nonstopmode" \
		-outdir=$(FIGURE_DIR)/anno_hist $< && \
	cd $(FIGURE_DIR)/anno_hist && latexmk -c

clean_figures:
	rm -f $(FIGURE_DIR)/anno_hist/histogram_f1.tex
	rm -f $(FIGURE_DIR)/anno_hist/histogram_cover.tex


##########
#        #
# Scores #
#        #
##########

.PHONY: score_files default_score_files oracle_score_files

score-dir:
	mkdir -p $(SCORE_DIR)

scores: default_scores oracle_scores

default_scores: \
	$(SCORE_DIR)/default_cover_scores.json \
	$(SCORE_DIR)/default_f1_scores.json

$(SCORE_DIR)/default_cover_scores.json: $(SCRIPT_DIR)/score_file.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | score-dir
	python $< -s $(SUMMARY_DIR) -e default -m cover > $@

$(SCORE_DIR)/default_f1_scores.json: $(SCRIPT_DIR)/score_file.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | score-dir
	python $< -s $(SUMMARY_DIR) -e default -m f1 > $@

oracle_scores: \
	$(SCORE_DIR)/oracle_cover_scores.json \
	$(SCORE_DIR)/oracle_f1_scores.json

$(SCORE_DIR)/oracle_cover_scores.json: $(SCRIPT_DIR)/score_file.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | score-dir
	python $< -s $(SUMMARY_DIR) -e oracle -m cover > $@

$(SCORE_DIR)/oracle_f1_scores.json: $(SCRIPT_DIR)/score_file.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | score-dir
	python $< -s $(SUMMARY_DIR) -e oracle -m f1 > $@

clean_score_files:
	rm -f $(SCORE_DIR)/default_cover_scores.json
	rm -f $(SCORE_DIR)/default_f1_scores.json
	rm -f $(SCORE_DIR)/oracle_cover_scores.json
	rm -f $(SCORE_DIR)/oracle_f1_scores.json

################################
#                              #
# Critical Difference Diagrams #
#                              #
################################

.PHONY: cd_diagrams clean_cd_diagrams

cdd-dir:
	mkdir -p $(CDD_DIR)

CD_DIAGRAMS=
define CDDiagram
CD_DIAGRAMS += $(CDD_DIR)/cddiagram_$(1)_$(2)_$(3).tex

$(CDD_DIR)/cddiagram_$(1)_$(2)_$(3).tex: \
	$(SCORE_DIR)/$(1)_$(2)_scores.json \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/rank_common.py \
	$(SCRIPT_DIR)/significance.py \
	$(SCRIPT_DIR)/critical_difference_diagram.py | cdd-dir
	python $(SCRIPT_DIR)/critical_difference_diagram.py -i $$< -o $$@ \
		-d $(3) -e $(1) -t wilcoxon -m $(MISSING_STRATEGY)
endef

$(foreach exp,$(EXPERIMENTS),\
	$(foreach metric,$(METRICS),\
	$(foreach dim,$(DIMENSIONALITY),\
	$(eval $(call CDDiagram,$(exp),$(metric),$(dim)))\
)))

cd_diagrams: $(CD_DIAGRAMS)

clean_cd_diagrams:
	rm -f $(CD_DIAGRAMS)

###############
#             #
#  Constants  #
#             #
###############

.PHONY: constants

CONSTANT_TARGETS = $(CONST_DIR)/sigtest_global_oracle_cover_uni.tex \
		   $(CONST_DIR)/sigtest_global_oracle_f1_uni.tex \
		   $(CONST_DIR)/sigtest_global_default_cover_uni.tex \
		   $(CONST_DIR)/sigtest_global_default_f1_uni.tex \
		   $(CONST_DIR)/SeriesLengthMin.tex \
		   $(CONST_DIR)/SeriesLengthMax.tex \
		   $(CONST_DIR)/SeriesLengthMean.tex \
		   $(CONST_DIR)/UniqueAnnotationsMin.tex \
		   $(CONST_DIR)/UniqueAnnotationsMax.tex \
		   $(CONST_DIR)/UniqueAnnotationsMean.tex \
		   $(CONST_DIR)/UniqueAnnotationsStd.tex

const-dir:
	mkdir -p $(CONST_DIR)

constants: $(CONSTANT_TARGETS)

$(CONST_DIR)/sigtest_global_oracle_cover_uni.tex: \
	$(SCORE_DIR)/oracle_cover_scores.json \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/rank_common.py \
	$(SCRIPT_DIR)/significance.py | const-dir
	python $(SCRIPT_DIR)/significance.py -i $< -o $@ -d univariate \
		--experiment oracle --mode global --missing $(MISSING_STRATEGY)

$(CONST_DIR)/sigtest_global_oracle_f1_uni.tex: \
	$(SCORE_DIR)/oracle_f1_scores.json \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/rank_common.py \
	$(SCRIPT_DIR)/significance.py | const-dir
	python $(SCRIPT_DIR)/significance.py -i $< -o $@ -d univariate \
		--experiment oracle --mode global --missing $(MISSING_STRATEGY)

$(CONST_DIR)/sigtest_global_default_cover_uni.tex: \
	$(SCORE_DIR)/default_cover_scores.json \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/rank_common.py \
	$(SCRIPT_DIR)/significance.py | const-dir
	python $(SCRIPT_DIR)/significance.py -i $< -o $@ -d univariate \
		--experiment oracle --mode global --missing $(MISSING_STRATEGY)

$(CONST_DIR)/sigtest_global_default_f1_uni.tex: \
	$(SCORE_DIR)/default_f1_scores.json \
	$(SCRIPT_DIR)/common.py $(SCRIPT_DIR)/rank_common.py \
	$(SCRIPT_DIR)/significance.py | const-dir
	python $(SCRIPT_DIR)/significance.py -i $< -o $@ -d univariate \
		--experiment oracle --mode global --missing $(MISSING_STRATEGY)

$(CONST_DIR)/SeriesLengthMin.tex: $(SCRIPT_DIR)/descriptive_length.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | const-dir
	python $< -s $(SUMMARY_DIR) -t min > $@

$(CONST_DIR)/SeriesLengthMax.tex: $(SCRIPT_DIR)/descriptive_length.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | const-dir
	python $< -s $(SUMMARY_DIR) -t max > $@

$(CONST_DIR)/SeriesLengthMean.tex: $(SCRIPT_DIR)/descriptive_length.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | const-dir
	python $< -s $(SUMMARY_DIR) -t mean > $@

$(CONST_DIR)/UniqueAnnotationsMin.tex: $(SCRIPT_DIR)/descriptive_annotations.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | const-dir
	python $< -s $(SUMMARY_DIR) -t min > $@

$(CONST_DIR)/UniqueAnnotationsMax.tex: $(SCRIPT_DIR)/descriptive_annotations.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | const-dir
	python $< -s $(SUMMARY_DIR) -t max > $@

$(CONST_DIR)/UniqueAnnotationsMean.tex: $(SCRIPT_DIR)/descriptive_annotations.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | const-dir
	python $< -s $(SUMMARY_DIR) -t mean > $@

$(CONST_DIR)/UniqueAnnotationsStd.tex: $(SCRIPT_DIR)/descriptive_annotations.py \
	$(SCRIPT_DIR)/common.py $(DATASET_SUMMARIES) | const-dir
	python $< -s $(SUMMARY_DIR) -t std > $@

clean_constants:
	rm -f $(CONSTANT_TARGETS)

###############
#             #
# Virtualenvs #
#             #
###############

.PHONY: venvs R_venv py_venvs venv_bocpdms venv_rbocpdms clean_venvs \
	clean_py_venv clean_R_venv

venvs: venv_bocpdms venv_rbocpdms R_venv

py_venvs: venv_bocpdms venv_rbocpdms

venv_bocpdms: ./execs/python/bocpdms/venv

./execs/python/bocpdms/venv:
	cd execs/python/bocpdms && python -m venv venv && \
		source venv/bin/activate && pip install wheel && \
		pip install -r requirements.txt

venv_rbocpdms: ./execs/python/rbocpdms/venv

./execs/python/rbocpdms/venv:
	cd execs/python/rbocpdms && python -m venv venv && \
		source venv/bin/activate && pip install wheel && \
		pip install -r requirements.txt

R_venv:
	bash ./utils/R_setup.sh Rpackages.txt ./execs/R/rlibs

clean_py_venv:
	rm -rf ./execs/python/bocpdms/venv
	rm -rf ./execs/python/rbocpdms/venv

clean_R_venv:
	rm -rf ./execs/R/rlibs
	rm -f ./.Rprofile ./.Renviron
	rm -f ./.Renviron

clean_venvs: clean_R_venv clean_py_venv

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

clean: clean_results clean_venvs

clean_results: clean_summaries clean_tables clean_constants
