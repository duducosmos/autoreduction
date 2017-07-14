#!/usr/bin/env python
# -*- Coding: UTF-8 -*-

_author = "E. S. Pereira"
_date = "14/06/2017"
_email = "pereira.somoza@gmail.com"

"""
Autonomos Reduction Script.

The file with info of tiles is in the formata tilesInfo_YYmmdd.txt
"""

import time
from datetime import datetime, timedelta
import sched
import os
from subprocess import check_call
import copy
import logging
from astropy.io import fits
import glob


class ReductionBot:

    def __init__(self, user, useremail,
                 clientIP="0.0.0.0",
                 searchFolder="/mnt/images",
                 deltaTimeHours=24,
                 workDir="./",
                 t80cam="./t80cam.yaml"
                 ):

        self.__scheduler = sched.scheduler(timefunc=time.time,
                                           delayfunc=time.sleep)
        self.__nextReduction = datetime.now()
        self.__deltaTimeHours = deltaTimeHours
        self._extra = {'clientip': clientIP, 'user': user}
        self._searchFolder = searchFolder

        self.t80cam = t80cam

        # Number of parallel linux process to insert image into Data Base
        self.nWorkers = 10
        self.dataListFile = ''

        self.biasList = []
        self.flatList = []
        self.observationList = {"mainSurvey": [], "ultraShort": []}

        self.existDataFolder = False

        self.useremail = useremail

        self.workDir = workDir

        self.outTileInfo = ""

        if(workDir[-1] == "/"):
            self.workDir += "reductionBotWDir/"
        else:
            self.workDir += "/reductionBotWDir/"

        if(os.path.isdir(self.workDir) is False):
            os.makedirs(self.workDir)

        if(os.path.isdir(self.workDir + "botLoggin") is False):
            os.makedirs(self.workDir + "botLoggin")

        self.logger = logging.getLogger()

        FORMAT = "%(asctime)-15s %(clientip)s %(user)-8s %(message)s"

        logginName = "reduction_{}.log".format(datetime.now().strftime(
            "%Y%m%dT%H:%M:%S")
        )

        self.insertDBLogFile = "insertDB_{}.log".format(datetime.now().strftime(
            "%Y%m%dT%H:%M:%S")
        )

        logging.basicConfig(filename=self.workDir + "/botLoggin/" + logginName,
                            level=logging.DEBUG,
                            format=FORMAT)

        self.logger.info("The Reduction Bot is Starting", extra=self._extra)

        self.dataListFile = "reduction_list_{}.txt".format(datetime.now().strftime(
            "%Y%m%dT%H:%M:%S")
        )

    def getNextReduction(self):
        return copy.copy(self.__nextReduction)

    def searchForNewData(self):
        folder = self._searchFolder

        searchFor = datetime.now() - timedelta(hours=24)

        if(folder[-1] == "/"):
            folder += searchFor.strftime("%Y%m%d")
        else:
            folder += "/" + searchFor.strftime("%Y%m%d")

        self.existDataFolder = os.path.isdir(folder)

        if(self.existDataFolder):
            self.logger.info("Selected folder for the current day: {}".format(folder),
                             extra=self._extra)
            return folder
        else:
            self.logger.error("No data folder for the current day: {}".format(folder),
                              extra=self._extra)
            return None

    def __separeteObsData(self, surveyData):

        self.logger.info("Separating in ultraShort and mainSurvey",
                         extra=self._extra)
        baseInfo = '''# 1 PNAME
# 2 RA
# 3 DEC
# 4 RADECsys_ID
# 5 PIXEL_SCALE
# 6 IMAGE_SIZE
'''
        tiles = {}
        tileEndName = datetime.now().strftime("%Y%m%d")

        for img in surveyData:
            imgExtension = img.split(".")[-1].replace("\n", "")
            hdu = fits.open(img.replace('\n', ''))
            if(imgExtension == "fz"):
                hd = hdu[1].header
                self.logger.warning("Image with header inverted: {}".format(img),
                                    extra=self._extra)
            else:
                hd = hdu[0].header

            if(hd['HIERARCH T80S DET EXPTIME'] <= 5.0):
                self.observationList['ultraShort'].append(img)
            else:
                if("OBJECT" in hd.keys()):
                    self.observationList['mainSurvey'].append(img)
                    if(hd["OBJECT"].replace(" ", "_") + tileEndName
                       not in tiles.keys()
                       ):

                        tiles[hd['OBJECT']] = [hd['CRVAL1'], hd['CRVAL2']]
                        baseInfo += "{0}_{1} {2} {3} 1 0.550 11000 \n".format(
                            hd['OBJECT'],
                            tileEndName,
                            hd['CRVAL1'],
                            hd['CRVAL2'])

                else:
                    self.logger.warning(
                        "No OBJECT key found in the header of image {}".format(
                            img),
                        extra=self._extra
                    )

        if(len(self.observationList['mainSurvey']) == 0):
            self.logger.warning("No Survey Data Found", extra=self._extra)
            return False

        self.outTileInfo = "tilesInfo_" + tileEndName + ".txt"

        self.logger.info(
            "Creating Tile Info File:  {}".format(
                self.workDir + self.outTileInfo),
            extra=self._extra
        )

        with open(self.workDir + self.outTileInfo, "w") as fOut:
            fOut.write(baseInfo)

        return True

    def __selectDataByType(self, folder):
        self.logger.info("Selecting data by Type", extra=self._extra)
        observedData = glob.glob(folder + "*.fits") + \
            glob.glob(folder + "*.fz")
        surveyData = []
        for img in observedData:
            imgName = img.split("/")[-1]
            if(imgName[0:3] == 'bia'):
                self.biasList.append(img)
            elif(imgName[0:3] == 'sky'):
                self.flatList.append(img)
            else:
                surveyData.append(img)

        if(len(self.biasList) == 0):
            self.logger.warning("No Bias Found", extra=self._extra)

        if(len(self.flatList) == 0):
            self.logger.warning("No Flat Found", extra=self._extra)

        if(len(surveyData) == 0):
            self.logger.warning("No Survey Data Found", extra=self._extra)
            return False

        self.__separeteObsData(surveyData)

        self.dataListFile = "reduction_list_{}.txt".format(
            datetime.now().strftime("%Y%m%dT%H:%M:%S")
        )

        with open(self.workDir + self.dataListFile, "w") as fOut:
            for iData in self.observationList['mainSurvey']:
                fOut.write("{}\n".format(iData))

            for iData in self.biasList:
                fOut.write("{}\n".format(iData))

            for iData in self.flatList:
                fOut.write("{}\n".format(iData))

        surveyDataFound = self.__separeteObsData(surveyData)
        return surveyDataFound

    def __addDataToDB(self):

        # Observation: The paralelization process was implemented using the
        # Linux xarg. System Dependent.

        self.logger.info("Adding data into DB.", extra=self._extra)

        commonCommand = "cat {0}|xargs -I ARG -P {1}".format(self.dataListFile,
                                                             self.nWorkers)

        self.logger.info("Step 1: Updating Header.", extra=self._extra)

        upHead = "{0} bash -c 'updatehead.py -i {1} -o \"$1\" >> {2}' fnord ARG".format(commonCommand,
                                                                 self.t80cam,
                                                                 self.workDir + self.insertDBLogFile)

        self.logger.info("Appling the command: {}".format(upHead),
                         extra=self._extra)

        try:
            check_call(upHead, shell=True)
        except:
            self.logger.error("An Error occurred during the updatehead",
                              extra=self._extra)
            return

        self.logger.info("Step 2: Classifing images.", extra=self._extra)

        imgClass = "{0} bash -c 'imgclassify.py -o \"$1\" >> {1}' fnord ARG ".format(commonCommand,
                                                             self.workDir + self.insertDBLogFile)

        self.logger.info("Appling the command: {}".format(imgClass),
                         extra=self._extra)

        try:
            check_call(imgClass, shell=True)
        except:
            self.logger.error("An Error occurred during the Image Classify",
                              extra=self._extra)
            return

        self.logger.info("Step 3: Inserting into DB.", extra=self._extra)

        inDb = "{0} bash -c 'insertdb.py -o \"$1\" >> {1}' fnord ARG".format(commonCommand,
                                                       self.workDir + self.insertDBLogFile)

        self.logger.info("Appling the command: {}".format(inDb),
                         extra=self._extra)

        try:
            check_call(inDb, shell=True)
        except:
            self.logger.error("An Error occurred during the db insert",
                              extra=self._extra)
            return

        self.logger.info(
            "Step 4: Inserting Tile Info into DB.", extra=self._extra)

        try:
            check_call("inserttiles.py {0} >> {1}".format(self.workDir + self.outTileInfo,
                                                          self.workDir + self.insertDBLogFile),
                       shell=True)
        except:
            self.logger.error("An Error occurred inseting tiles info",
                              extra=self._extra)
            return

    def __startReduction(self):
        self.logger.info("Starting the reduction process", extra=self._extra)

    def steps(self):
        folder = self.searchForNewData()
        if(folder is not None):
            surveyDataFound = self.__selectDataByType(folder + "/")
            if(surveyDataFound):
                self.__addDataToDB()
                self.__startReduction()

    def rescheduler(self):
        self.logger.info("Starting Scheduler", extra=self._extra)
        self.__nextReduction = datetime.now()
        self.__nextReduction += timedelta(hours=self.__deltaTimeHours)

        self.steps()

        self.logger.info(
            "Next reduction will be started at: {}".format(
                self.__nextReduction),
            extra=self._extra
        )

        self.biasList = []
        self.flatList = []
        self.observationList = {"mainSurvey": [], "ultraShort": []}

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

    bot = ReductionBot(user="jype",
                       useremail="pereira.somoza@gmail.com",
                       deltaTimeHours=24)
    bot.startBot()
