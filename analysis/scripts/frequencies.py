# -*- coding: utf-8 -*-

"""
Table of frequencies for the time series.

Author: Gertjan van den Burg
Copyright (c) 2021 - The Alan Turing Institute
License: See the LICENSE file.

"""

from common import Dataset

FREQUENCIES = {
    Dataset.apple: "Daily$^{\dagger}$",
    Dataset.bank: "Daily",
    Dataset.bee_waggle_6: "Unit",
    Dataset.bitcoin: "Daily$^{\dagger}$",
    Dataset.brent_spot: "Fortnightly",
    Dataset.businv: "Monthly",
    Dataset.centralia: "Decenially",
    Dataset.children_per_woman: "Yearly",
    Dataset.co2_canada: "Yearly",
    Dataset.construction: "Monthly",
    Dataset.debt_ireland: "Yearly",
    Dataset.gdp_argentina: "Yearly",
    Dataset.gdp_croatia: "Yearly",
    Dataset.gdp_iran: "Yearly",
    Dataset.gdp_japan: "Yearly",
    Dataset.global_co2: "Quadrennial",
    Dataset.homeruns: "Yearly",
    Dataset.iceland_tourism: "Monthly",
    Dataset.jfk_passengers: "Monthly",
    Dataset.lga_passengers: "Monthly",
    Dataset.nile: "Yearly",
    Dataset.occupancy: "Every 16 min.",
    Dataset.ozone: "Yearly",
    Dataset.quality_control_1: "Unit",
    Dataset.quality_control_2: "Unit",
    Dataset.quality_control_3: "Unit",
    Dataset.quality_control_4: "Unit",
    Dataset.quality_control_5: "Unit",
    Dataset.rail_lines: "Yearly",
    Dataset.ratner_stock: "Daily$^{\dagger}$",
    Dataset.robocalls: "Monthly",
    Dataset.run_log: "Every 5 sec.",
    Dataset.scanline_126007: "Unit",
    Dataset.scanline_42049: "Unit",
    Dataset.seatbelts: "Monthly",
    Dataset.shanghai_license: "Monthly",
    Dataset.uk_coal_employ: "Yearly",
    Dataset.measles: "Weekly",
    Dataset.unemployment_nl: "Yearly",
    Dataset.us_population: "Monthly",
    Dataset.usd_isk: "Monthly",
    Dataset.well_log: "Unit",
}
