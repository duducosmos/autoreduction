#!/usr/bin/env python
# -*- Coding: UTF-8 -*-


"""
__init__               :  1
GetSciImages           :  2
prepare_catalogs       :  3
do_internal_astro      :  4
do_internal_photo      :  5
SwarpImages            :  6
CreateObjMask          :  7
MaskImprove            :  8
ComputeIndCatalog      :  9
ComputeDualModeCatalog :  10
ReferenceFilterMissing :  11
UpdateTile             :  12
Complete               :  0
"""

coaddingError = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

JYPE_VERSION = "MainSurvey"
PATH_ROOT = "/home/ed"
TILES_VERSION = "T01"
RAW_PATH_PATTERN = "/mnt/images"
dbname = "main_survey"
dbuserName = "jypesql"
passdb = "jypesql"

MIN_COMBINE_NUMBER_FLAT = 3
MIN_COMBINE_NUMBER_BIAS = 3

FILTERS = ('R', 'I', 'G', 'F660', 'U', 'Z',
           'F378', 'F395', 'F410', 'F861',
           'F515', 'F430'
           )
