#!/usr/bin/env python
# -*- Coding: UTF-8 -*-

_author = "E. S. Pereira"
_date = "15/06/2017"
_email = "pereira.somoza@gmail.com"

from model import db

def searchImages(startDate, endDate, frametype, filt):
    """
    Return the Number of images in the Pipeline Data Base.
    """
    typeID = db(db.frametype.Name == frametype).select(db.frametype.id).first()
    nimages = 0
    if(frametype == "BIAS"):
        nimages = db((db.t80oa.ImageType_ID == typeID)
                     &
                     (db.t80oa.Date >= startDate)
                     &
                     (db.t80oa.Date <= endDate)
                     ).count()
    else:
        filterID = db(db.filter.Name == filt).select(db.filter.id).first()
        nimages = db((db.t80oa.ImageType_ID == typeID)
                     &
                     (db.t80oa.Filter_ID == filterID)
                     &
                     (db.t80oa.Date >= startDate)
                     &
                     (db.t80oa.Date <= endDate)
                     ).count()
    return nimages
