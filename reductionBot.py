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
from config import JYPE_VERSION, RAW_PATH_PATTERN
from config import FILTERS, MIN_COMBINE_NUMBER_FLAT, MIN_COMBINE_NUMBER_BIAS
from searchImages import searchImages


class ReductionBot:
    '''
    Reduction Bot Version 0.1
    '''

    def __init__(self, user, useremail,
                 clientIP="0.0.0.0",
                 deltaTimeHours=24,
                 workDir="./",
                 t80cam="./t80cam.yaml",
                 instConfig="./instr-t80cam.txt",
                 deltaDaysFlatBias=10
                ):

        self.__scheduler = sched.scheduler(timefunc=time.time,
                                           delayfunc=time.sleep)
        self.__nextReduction = datetime.now()
        self.__deltaTimeHours = deltaTimeHours
        self._extra = {'clientip': clientIP, 'user': user}

        self._searchFolder = RAW_PATH_PATTERN
        self.outReducFolder = JYPE_VERSION

        self.t80cam = t80cam

        # Number of parallel linux process to insert image into Data Base
        self.nWorkers = 10

        self.biasList = []
        self.flatList = []
        self.observationList = {"mainSurvey": [], "ultraShort": []}
        self.tiles = []

        self.existDataFolder = False

        self.useremail = useremail

        self.workDir = workDir

        self.instConfig = instConfig

        self.deltaDaysFlatBias = deltaDaysFlatBias

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

        self.dataListFile = None

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
            self.logger.info("Selected folder for the current day: {}".format(
                folder),
                extra=self._extra)
            return folder
        else:
            self.logger.error("No data folder for the current day: {}".format(
                folder),
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

        tileEndName = datetime.now().strftime("%Y%m%d")

        for img in surveyData:
            imgExtension = img.split(".")[-1].replace("\n", "")
            hdu = fits.open(img.replace('\n', ''))

            headerInHDU0 = True

            try:
                hd = hdu[0].header
                hd['HIERARCH T80S DET EXPTIME']
            except:
                headerInHDU0 = False
                self.logger.error("Header not in HDU 0 : {}".format(img),
                                  extra=self._extra)

            if(headerInHDU0 is True):

                if(hd['HIERARCH T80S DET EXPTIME'] <= 5.0):
                    self.observationList['ultraShort'].append(img)
                else:
                    if("OBJECT" in hd.keys()):
                        self.observationList['mainSurvey'].append(img)
                        tileName = "{0}_{1}".format(hd['OBJECT'].replace(" ", "_"),
                                                    tileEndName)
                        if(tileName not in self.tiles
                           ):

                            self.tiles.append(tileName)

                            baseInfo += "{0} {1} {2} 1 0.550 11000 \n".format(
                                tileName,
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

        surveyDataFound = False
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
        else:
            surveyDataFound = self.__separeteObsData(surveyData)

        self.dataListFile = self.workDir + "reduction_list_{}.txt".format(
            datetime.now().strftime("%Y%m%d")
        )

        with open(self.dataListFile, "w") as fOut:
            for iData in self.observationList['mainSurvey']:
                fOut.write("{}\n".format(iData))

            for iData in self.biasList:
                fOut.write("{}\n".format(iData))

            for iData in self.flatList:
                fOut.write("{}\n".format(iData))


        return surveyDataFound

    def __addDataToDB(self, dataListFile, insertTiles=True):

        # Observation: The paralelization process was implemented using the
        # Linux xarg. System Dependent.

        self.logger.info("Adding data into DB.", extra=self._extra)

        commonCommand = "cat {0}|xargs -I ARG -P {1}".format(dataListFile,
                                                             self.nWorkers)

        self.logger.info("Step 1: Updating Header.", extra=self._extra)

        upHead = "{0} bash -c 'updatehead.py -i {1} -o \"$1\" >> {2}' fnord ARG".format(
            commonCommand,
            self.t80cam,
            self.workDir + self.insertDBLogFile)

        self.logger.info("Appling the command: {}".format(upHead),
                         extra=self._extra)

        try:
            check_call(upHead, shell=True)
        except:
            self.logger.error("An Error occurred during the updatehead",
                              extra=self._extra)
            return False

        self.logger.info("Step 2: Classifing images.", extra=self._extra)

        imgClass = "{0} bash -c 'imgclassify.py -o \"$1\" >> {1}' fnord ARG ".format(
            commonCommand,
            self.workDir + self.insertDBLogFile)

        self.logger.info("Appling the command: {}".format(imgClass),
                         extra=self._extra)

        try:
            check_call(imgClass, shell=True)
        except:
            self.logger.error("An Error occurred during the Image Classify",
                              extra=self._extra)
            return False

        self.logger.info("Step 3: Inserting into DB.", extra=self._extra)

        inDb = "{0} bash -c 'insertdb.py -o \"$1\" >> {1}' fnord ARG".format(
            commonCommand,
            self.workDir + self.insertDBLogFile)

        self.logger.info("Appling the command: {}".format(inDb),
                         extra=self._extra)

        try:
            check_call(inDb, shell=True)
        except:
            self.logger.error("An Error occurred during the db insert",
                              extra=self._extra)
            return False

        if(insertTiles is True):
            self.logger.info(
                "Step 4: Inserting Tile Info into DB.", extra=self._extra)

            try:
                check_call("inserttiles.py {0} >> {1}".format(
                    self.workDir + self.outTileInfo,
                    self.workDir + self.insertDBLogFile),
                    shell=True)
            except:
                self.logger.error("An Error occurred inserting tiles info",
                                  extra=self._extra)
                return False

        return True

    def hasAllFlats(self):
        """
        Determine the start day for the reduction
        From the minimum Flat necessary.
        """
        endDate = datetime.now().date()
        startDate = datetime.now() - timedelta(hours=self.deltaDaysFlatBias * 24)
        startDate = start.date()

        needMoreFlat = []

        for filt in FILTERS:
            nFilt = searchImages(startDate, endDate, "FLAS", filt)
            if(nFilt < MIN_COMBINE_NUMBER_FLAT):
                self.logger.warning(
                    "Need More Flat for Filt {0}.".format(filt),
                    extra=self._extra)
                needMoreFlat.append(filt)

        if(len(needMoreFlat) == 0):
            return True, startDate.strftime("%Y-%m-%d")
        else:
            return False, needMoreFlat

    def __searchForFlats(self, searchWindow, filts):
        self.logger.info("Starting to search for Flat in filter {0}".format(filt),
                         extra=self._extra)
        flatsByDay = {datetime.strptime(swi.split("/")[-1],  "%Y%m%d").date():
                      glob.glob(swi + "/skyflat*")
                      for swi in searchWindow
                      }
        flatsByFilter = {}

        for key, value in flatsByDay.items():

            for img in value:
                hdu = fits.open(img.replace('\n', ''))

                headerInHDU0 = True

                try:
                    hd = hdu[0].header
                    hd['HIERARCH T80S DET EXPTIME']
                except:
                    headerInHDU0 = False
                    self.logger.error("Header not in HDU 0 : {}".format(img),
                                      extra=self._extra)

                if(headerInHDU0 is True):
                    currentFilter = hd["FILTER"]
                    if(currentFilter not in flatsByFilter.keys()):
                        flatsByFilter[currentFilter] = {'date': key,
                                                        'flats': [img]
                                                        }
                    else:
                        nIFilt = len(flatsByFilter[currentFilter])
                        if(nIFilt < MIN_COMBINE_NUMBER_FLAT):

                            flatsByFilter[currentFilter]['date'] = min(
                                flatsByFilter[currentFilter]['date'],
                                key
                            )

                            flatsByFilter[currentFilter]['flats'].append(img)

                            if(nIFilt + 1 == MIN_COMBINE_NUMBER_FLAT):
                                self.logger.info(
                                    "Last Flat found at {0} for {1}.".format(
                                        key,
                                        currentFilter),
                                    extra=self._extra)

        return flatsByFilter

    def searchForFlats(self, needMoreFlat):

        self.logger.info("Starting to search for Flat in previous days process",
                         extra=self._extra)
        self.logger.info("The search will be on the window of {0} days".format(
            self.deltaDaysFlatBias),
            extra=self._extra)

        folder = self._searchFolder

        def foldDateName(i): return datetime.now() - timedelta(days=i)

        searchWindow = [foldDateName(i).strftime("%Y%m%d")
                        for i in range(2, self.deltaDaysFlatBias + 1)
                        ]

        if(folder[-1] == "/"):
            searchWindow = [folder + swi for swi in searchWindow
                            if os.path.isdir(folder + swi) == True]
        else:
            searchWindow = [folder + "/" + swi for swi in searchWindow
                            if os.path.isdir(folder + "/" + swi) == True]

        if(len(searchWindow) == 0):
            self.logger.error("No data folder found in the Search Window.",
                              extra=self._extra)
            return False

        flatsFound = self.__searchForFlats(searchWindow, needMoreFlat)

        if(len(flatsFound.keys()) == 0):
            self.logger.error("No Flats found in the Search Window.",
                              extra=self._extra)
            return False

        if(len(flatsFound.keys()) < len(needMoreFlat)):
            self.logger.warning("No All Need Flats found in the Search Window.",
                                extra=self._extra)

        startDay, flatsInserted = self.__insertNewFlats(flatsFound)
        return flatsInserted, startDay

    def __insertNewFlats(self, flatsFound):

        startDay = datetime.now().date()

        if(self.workDir[-1] == "/"):

            newsFlatFile = self.workDir + "newsFlat_list_{}.txt".format(
                datetime.now().strftime("%Y%m%d")
            )
        else:
            newsFlatFile = self.workDir + "/newsFlat_list_{}.txt".format(
                datetime.now().strftime("%Y%m%d")
            )

        with open(newsFlatFile, "w") as fOut:
            for keys, values in flatsFound.items():
                startDay = min(values['date'], startDay)
                for fi in values['flats']:
                    fOut.write("{}\n".format(fi))

        return startDay.strftime("%Y-%m-%d"), self.__addDataToDB(newsFlatFile, insertTiles=False)


    def __startReduction(self, startReduction):
        self.logger.info("Starting the reduction process", extra=self._extra)
        endReduction = datetime.now().strftime("%Y-%m-%d")

        for tile in self.tiles:
            command = "autoJypeReductionTile.sh {0} {1} {2} {3} {4} {5}".format(
                startReduction,
                endReduction,
                instConfig,
                tile,
                self.outReducFolder,
                self.useremail
            )
            try:
                check_call(command,
                           shell=True)
                self.logger.info(
                    "Reducion for Tile {0} end.".format(tile),
                    extra=self._extra)
            except:
                self.logger.error(
                    "An Error occurred for the reducion of Tile: {0}".format(
                        tile),
                    extra=self._extra)

    def __subStep1(self):
        dataInserted = self.__addDataToDB(self.dataListFile)
        if(dataInserted is True):
            hasFlats = self.hasAllFlats()
            if(hasFlats[0] == True):
                self.__startReduction(hasFlats[1])
            else:
                self.logger.warning(
                    "No all necessary flats found. Starting The Flat Search.",
                    extra=self._extra)
                flatsInserted, startDay = self.searchForFlats(hasFlats[1])
                if(flatsInserted == False):
                    self.logger.error(
                        "No flats found.",
                        extra=self._extra)
                else:
                    self.__startReduction(startDay)


    def steps(self):
        folder = self.searchForNewData()
        if(folder is not None):
            surveyDataFound = self.__selectDataByType(folder + "/")
            if(surveyDataFound is True):
                self.__subStep1()
            else:
                if(len(self.biasList) != 0 or len(self.flatList) != 0):
                    dataInserted = self.__addDataToDB(self.dataListFile,
                                                      insertTiles=False)




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
        self.tiles = []

        self.__scheduler.enterabs(time.mktime(self.__nextReduction.timetuple()),
                                  priority=0,
                                  action=self.rescheduler, argument=())

    def __setStartTime(self, hour, minute):
        currentTime = datetime.now()
        setTime = currentTime.replace(hour=hour, minute=minute)
        deltaTime = setTime - currentTime
        if(deltaTime.total_seconds() < 0):
            nextTime = currentTime + timedelta(hours=12)
            nextTime = nextTime.replace(hour=hour, minute=minute)
        else:
            nextTime = setTime
        self.logger.info(
            "The reduction will be started at: {}".format(nextTime),
            extra=self._extra
        )
        self.__scheduler.enterabs(time.mktime(nextTime.timetuple()),
                                  priority=0,
                                  action=self.rescheduler, argument=())

    def startBot(self, hour, minute):
        self.__setStartTime(hour, minute)
        try:
            self.__scheduler.run()
        except KeyboardInterrupt:
            print("Stopping")


if(__name__ == "__main__"):
    import argparse
    description = '''Autonomos Reduction Bot.
    The Bot Search for observed data in the last night and start the
    reduction process, if it found new data.
    '''
    parser = argparse.ArgumentParser(
        description=description)

    parser.add_argument("-u",
                        help="User Name",
                        type=str,
                        default="jype")

    parser.add_argument("-e",
                        help="User email",
                        type=str,
                        default="pereira.somoza@gmail.com")

    parser.add_argument("-t",
                        help="Time interval, in hours, for the next reduction",
                        type=int,
                        default=24)

    parser.add_argument("-d",
                        help="Time interval, in days, to search for Flat and Bias",
                        type=int,
                        default=20)

    args = parser.parse_args()

    bot = ReductionBot(user=args.u,
                       useremail=args.e,
                       deltaTimeHours=args.t,
                       deltaDaysFlatBias=args.d)
    bot.startBot(7, 0)
