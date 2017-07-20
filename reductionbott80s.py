#!/usr/bin/env python
# -*- Coding: UTF-8 -*-
"""
Reduction Bot for T80S Telescope:
This module containg the class that perform the reduction process every day
in a given time.
"""
import time
from datetime import datetime, timedelta
import sched
import os
from subprocess import check_call, CalledProcessError
import copy
import logging

from astropy.io import fits

from config import JYPE_VERSION
from config import FILTERS, MIN_COMBINE_NUMBER_FLAT, MIN_COMBINE_NUMBER_BIAS
from config import INSTRUMENT_CONFIG_FILE, RAW_PATH_PATTERN
from searchimages import count_images, search_images

__AUTHOR = "E. S. Pereira"
__DATE = "14/06/2017"
__EMAIL = "pereira.somoza@gmail.com"


class ReductionBotT80S(object):
    """
    Reductio Bot: Used to administrate the autonomous reduction process.
    """

    def __init__(self,
                 user,
                 useremail,
                 **kwargs):

        client_ip = "localhost"
        self._delta_time_hours = 24,
        self._work_dir = "./"
        self._delta_days_fb = 15

        allowed_keys = set(['client_ip',
                            'delta_time_hours',
                            'work_dir',
                            'delta_days_fb'])

        self._scheduler = sched.scheduler(timefunc=time.time,
                                          delayfunc=time.sleep)
        self._next_reduction = datetime.now()
        self.useremail = useremail

        if kwargs is not None:
            for key, value in kwargs.items():
                if key in allowed_keys:
                    if key == 'client_ip':
                        client_ip = value
                    else:
                        setattr(self, '_' + key, value)

        self._extra = {'clientip': client_ip, 'user': user}

        if self._work_dir[-1] == "/":
            self._work_dir += "reductionBotWDir/"
        else:
            self._work_dir += "/reductionBotWDir/"

        if os.path.isdir(self._work_dir) is False:
            os.makedirs(self._work_dir)

        if os.path.isdir(self._work_dir + "botLoggin") is False:
            os.makedirs(self._work_dir + "botLoggin")

        self._logger = logging.getLogger()

        _format = "%(asctime)-15s %(clientip)s %(user)-8s %(message)s"

        loggin_name = "reduction_{}.log".format(
            datetime.now().strftime("%Y%m%dT%H:%M:%S"))

        logging.basicConfig(filename=self._work_dir + "/botLoggin/" + loggin_name,
                            level=logging.DEBUG,
                            format=_format)

        self._logger.info("The Reduction Bot is Starting", extra=self._extra)

    def get_next_reduction(self):
        """
        Return a date object representing the next reduction date time.
        """
        return copy.copy(self._next_reduction)

    def has_all_flats(self):
        """
        Return True and start date if all need flats were found in the pipeline
        database, else, return false and the list of filters that need more
        flats.
        """
        end_date = datetime.now().date()
        start_date = datetime.now() - timedelta(days=self._delta_days_fb)
        start_date = start_date.date()

        need_more_flats = []

        for filt in FILTERS:
            nflats = count_images(start_date, end_date, "FLAS", filt)
            if nflats < MIN_COMBINE_NUMBER_FLAT:
                info = "Need More Flat for Filt {0}.  Found {1}.".format(filt, nflats)
                self._logger.error(info, extra=self._extra)
                need_more_flats.append(filt)

        if len(need_more_flats) == 0:
            return True
        else:
            return False, need_more_flats

    def has_all_bias(self):
        """
        Return True if all nedd bias was found, else, return False.
        """

        end_date = datetime.now().date()
        start_date = datetime.now() - timedelta(days=self._delta_days_fb)
        start_date = start_date.date()
        nbias = count_images(start_date, end_date, "BIAS")
        if nbias < MIN_COMBINE_NUMBER_BIAS:
            info = "Found only {0} Bias.".format(nbias)
            self._logger.error(info, extra=self._extra)
            return False
        return True

    def _gen_tiles_info(self):
        '''
        Get scientific image and generate the tile info
        '''
        base_info = '''# 1 PNAME
    # 2 RA
    # 3 DEC
    # 4 RADECsys_ID
    # 5 PIXEL_SCALE
    # 6 IMAGE_SIZE
    '''

        tiles = []

        for filt in FILTERS:
            s_date = datetime.now() - timedelta(days=1)
            s_date = s_date.date()
            imgs = search_images(s_date, s_date, "SCIE", filt=filt)
            for img in imgs:
                imgf = None

                if RAW_PATH_PATTERN[-1] == "/":
                    img_loc = RAW_PATH_PATTERN + img
                else:
                    img_loc = RAW_PATH_PATTERN + '/' + img

                for ext in ['fits', 'fits.fz', 'fz']:
                    if os.path.isfile(img_loc + ext):
                        imgf = img_loc + ext
                        break
                if imgf is not None:
                    hdu = fits.open(imgf)

                    try:
                        hd = hdu[0].header
                        hd['HIERARCH T80S DET EXPTIME']
                    except KeyError:
                        hd = hdu[1].header
                        info = "Header not in HDU 0 : {}".format(img)
                        self._logger.error(info, extra=self._extra)

                    if "OBJECT" in hd.keys():
                        tile_name = hd['OBJECT']
                        if tile_name not in tiles:
                            tiles.append(tile_name)
                            base_info += "{0} {1} {2} 1 0.550 11000 \n".format(
                                tile_name,
                                hd['CRVAL1'],
                                hd['CRVAL2'])
                    else:
                        info = "No OBJECT key found in the header of image {}".format(
                            img)
                        self._logger.warning(info, extra=self._extra)

        return tiles, base_info

    def _insert_tiles_info(self):
        '''
        Get scientific image and generate the tile info
        '''

        tiles, base_info = self._gen_tiles_info()

        if len(tiles) != 0:
            tname = self._work_dir
            tname += "tilesInfo_" + datetime.now().strftime("%Y%m%d") + ".txt"
            with open(tname, 'w') as fout:
                fout.write(base_info)

            self._logger.info(
                "Inserting Tile Info into DB.", extra=self._extra)
            try:
                out_log = self._work_dir
                out_log += "insert_tiles_" + datetime.now().strftime("%Y%m%d") + ".log"
                check_call("inserttiles.py {0} >> {1}".format(tname, out_log),
                           shell=True)
            except CalledProcessError:
                self._logger.error("An Error occurred inserting tiles info",
                                   extra=self._extra)
                return False
            return tiles
        return False

    def _start_reduction(self):
        self._logger.info("Starting the reduction process", extra=self._extra)
        end_reduction = datetime.now().strftime("%Y-%m-%d")
        start_date = datetime.now() - timedelta(days=self._delta_days_fb)
        start_date = start_date.strftime("%Y-%m-%d")

        tiles = self._insert_tiles_info()
        if tiles is not False:
            for tile in tiles:
                command = "reductionJypeT80S.sh {0} {1} {2} {3} {4} {5}".format(
                    start_date,
                    end_reduction,
                    INSTRUMENT_CONFIG_FILE,
                    tile,
                    JYPE_VERSION,
                    self.useremail
                )
                try:
                    check_call(command,
                               shell=True)
                    info = "Reducion for Tile {0} end.".format(tile)
                    self._logger.info(info, extra=self._extra)
                except CalledProcessError:
                    info = "An Error occurred for the reducion of Tile: {0}".format(
                        tile)
                    self._logger.error(info, extra=self._extra)

    def _rescheduler(self):
        self._next_reduction = datetime.now() + timedelta(hours=self._delta_time_hours)

        if self.has_all_bias() is True:
            if self.has_all_flats() is True:
                self._start_reduction()

        info = "Next reduction will be started at: {}".format(
            self._next_reduction)

        self._logger.info(info, extra=self._extra)

        self._scheduler.enterabs(time.mktime(self._next_reduction.timetuple()),
                                 priority=0,
                                 action=self._rescheduler,
                                 argument=())

    def _set_time(self, hours, minutes):
        """
        Set the start time of the reduction process.
        """
        current_time = datetime.now()
        set_time = current_time.replace(hour=hours, minute=minutes)
        delta_time = set_time - current_time
        if delta_time.total_seconds() < 0:
            next_time = current_time + timedelta(hours=12)
            next_time = next_time.replace(hour=hours, minute=minutes)
        else:
            next_time = set_time

        self._next_reduction = next_time
        info = "Next reduction will be started at: {}".format(
            self._next_reduction)

        self._logger.info(info, extra=self._extra)

        self._scheduler.enterabs(time.mktime(next_time.timetuple()),
                                 priority=0,
                                 action=self._rescheduler,
                                 argument=())

    def run(self, hours, minutes):
        """
        Start the scheduler to run the reduction in autonomous mode.
        """
        self._set_time(hours, minutes)
        try:
            self._scheduler.run()
        except KeyboardInterrupt:
            print("Stopping")


if __name__ == "__main__":
    import argparse
    DESCRIPTION = '''Autonomos Reduction Bot.
    The Bot Search for observed data in the last night and start the
    reduction process, if it found new data.
    '''
    PARSER = argparse.ArgumentParser(
        description=DESCRIPTION)

    PARSER.add_argument("-u",
                        help="User Name",
                        type=str,
                        default="jype")

    PARSER.add_argument("-e",
                        help="User email",
                        type=str,
                        default="pereira.somoza@gmail.com")

    PARSER.add_argument("-t",
                        help="Time interval, in hours, for the next reduction",
                        type=int,
                        default=24)

    PARSER.add_argument("-d",
                        help="Time interval, in days, to search for Flat and Bias",
                        type=int,
                        default=20)

    ARGS = PARSER.parse_args()

    bot = ReductionBotT80S(user=ARGS.u,
                           useremail=ARGS.e,
                           delta_time_hours=ARGS.t,
                           delta_days_fb=ARGS.d)
    bot.run(7, 0)
