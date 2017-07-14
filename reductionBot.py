#!/usr/bin/env python
# -*- Coding: UTF-8 -*-

_author = "E. S. Pereira"
_date = "14/06/2017"
_email = "pereira.somoza@gmail.com"

"""
Autonomos Reduction Script.
"""

import time
from datetime import datetime, timedelta
import sched
import os
import copy
import logging

logger = logging.getLogger()


class ReductionBot:

    def __init__(self, user, useremail, clientIP="0.0.0.0", searchFolder="/mnt/images",
                 deltaTimeHours=24):
        self.__scheduler = sched.scheduler(timefunc=time.time,
                                           delayfunc=time.sleep)
        self.__nextReduction = datetime.now()
        self.__deltaTimeHours = deltaTimeHours
        self._extra = {'clientip': clientIP, 'user': user}
        self._searchFolder = searchFolder

        self.biasList = []
        self.flatList = []
        self.observationList = []

        self.existDataFolder = False

        self.useremail = useremail

        logger.info("Starting bot", extra=self._extra)

    def getNextReduction(self):
        return copy.copy(self.__nextReduction)

    def searchForNewData(self):
        folder = self._searchFolder

        if(folder[-1] == "/"):
            folder += datetime.now().strftime("%Y%m%d")
        else:
            folder += "/" + datetime.now().strftime("%Y%m%d")

        self.existDataFolder = os.path.isdir(folder)

        if(self.existDataFolder):
            logger.info("Selected folder for the current day: {}".format(folder),
                        extra=self._extra)
            return folder
        else:
            logger.error("No data folder for the current day: {}".format(folder),
                         extra=self._extra)
            return None

    def __selectDataByType(self, folder):
        logger.info("Selecting data by Type", extra=self._extra)

    def __selectObsData(self):
        logger.info("Separating observational data by time integration",
                    extra=self._extra)

    def __addDataToDB(self):
        logger.info("Starting to add data into DB", extra=self._extra)

    def __creatingTileInfo(self):
        logger.info("Creating tile info", extra=self._extra)

    def __startReduction(self):
        logger.info("Starting the reduction process", extra=self._extra)

    def steps(self):
        folder = self.searchForNewData()
        if(folder is not None):
            self.__selectDataByType(folder)
            self.__selectObsData1()
            self.__addDataToDB()
            self.__creatingTileInfo()
            self.__startReduction()

    def rescheduler(self):
        logger.info("Starting Scheduler", extra=self._extra)
        self.__nextReduction = datetime.now()
        self.__nextReduction += timedelta(hours=self.__deltaTimeHours)

        self.steps()

        logger.info(
            "Next reduction will be started at: {}".format(
                self.__nextReduction),
            extra=self._extra
        )

        self.biasList = []
        self.flatList = []
        self.observationList = []

        self.__scheduler.enterabs(time.mktime(self.__nextReduction.timetuple()),
                                  priority=0,
                                  action=self.rescheduler, argument=())

    def startBot(self):
        self.rescheduler()
        try:
            self.__scheduler.run()
        except KeyboardInterrupt:
            print("Stopping")


if(__name__ == "__main__"):
    FORMAT = "%(asctime)-15s %(clientip)s %(user)-8s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    bot = ReductionBot(user="jype",
                       useremail="pereira.somoza@gmail.com",
                       deltaTimeHours=1.0 / (60 * 8))
    bot.startBot()
