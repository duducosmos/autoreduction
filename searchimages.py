#!/usr/bin/env python
# -*- Coding: UTF-8 -*-
"""
Search for images in the Pipeline Data Base.
"""
from datetime import datetime, timedelta
from model import db

__AUTHOR = "E. S. Pereira"
__DATE = "15/06/2017"
__EMAIL = "pereira.somoza@gmail.com"


def search_images(date, frametype, filt=None):
    """
    Return the available images in a given day.
    """

    type_id = db(db.frametype.Name == frametype).select(db.frametype.id).first()
    nimages = 0
    if frametype == "BIAS":
        nimages = db((db.t80oa.ImageType_ID == type_id)
                     &
                     (db.t80oa.Date == date)).select(db.t80oa.Name)
        nimages = [img.Name for img in nimages]
    else:
        if filt != None:
            filter_id = db(db.filter.Name == filt).select(db.filter.id).first()
            nimages = db((db.t80oa.ImageType_ID == type_id)
                         &
                         (db.t80oa.Filter_ID == filter_id)
                         &
                         (db.t80oa.Date == date)).select(db.t80oa.Name)
            nimages = [img.Name for img in nimages]
        else:
            raise NameError("No Filter Passed")
    return nimages


def count_images(start_date, end_date, frametype, filt=None):
    """
    Return the Number of images in the Pipeline Data Base.
    """
    type_id = db(db.frametype.Name == frametype).select(db.frametype.id).first()
    nimages = 0
    if frametype == "BIAS":
        nimages = db((db.t80oa.ImageType_ID == type_id)
                     &
                     (db.t80oa.Date >= start_date)
                     &
                     (db.t80oa.Date <= end_date)).count()
    else:
        if filt != None:
            filter_id = db(db.filter.Name == filt).select(db.filter.id).first()
            nimages = db((db.t80oa.ImageType_ID == type_id)
                         &
                         (db.t80oa.Filter_ID == filter_id)
                         &
                         (db.t80oa.Date >= start_date)
                         &
                         (db.t80oa.Date <= end_date)).count()
        else:
            raise NameError("No Filter Passed")
    return nimages
