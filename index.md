# T80S Autonomous Reduction Robot

The autonomous reduction bot was written in python and shell script.
The program use the jype pipeline to reduce the data. The core of the robot is the script called `reductionJypeT80S.sh`.
In the `reductionJypeT80S.sh` script is organized all reduction process, from the creation of master frames until the images combinations.

## Jype Installation

The Jype installer process is described [here](install.md)

## The Reduction Script

The `reductionJypeT80S.sh` is optimized to generate the master flats in parallel in groups of four filters. This parallelization was optimized for a multi-core machine, and, it can be used independently of the reduction bot. This script represent the automation of the reduction process using jype pipeline.

The first step to use this script is activate the python virtual environment with the command:

```bash
source /home/jype/jype/miniconda/bin/activate jype_t80s
```

Note that the last parameter `jype_t80s` represent the name of the virtual env.

The `reductionJypeT80S.sh` receive six input parameters:

1. The **first** parameter is the start reduction date and the **second** parameter is the en reduction date. The date must be  in the format of `yyyy-mm-dd`, being `yyyy` the year, `mm` the month and `dd` the day.
2. The third parameter is the instrument configuration file, e.g.,  `instr-t80cam.txt`.
3. The fourth parameter is the tile name.
4. The fifth parameter is the name of the folder where the pipeline save the date. This name is defined in the configuration file of the jype pipeline and it is represented by JYPE_VERSION.
5. The last parameter is an e-mail. When the script end, a e-mail is send for the user, informing that the reduction process is finished.

The use of the reduction script is:

```bash
reductionJypeT80S.sh 2016-09-08 2016-09-11 instr-t80cam.txt STRIPE82_0021 STRIPE82 use.email@gmail.com
```

If we are using this script by ssh, in a remote server, it is recommended to run the reduction in background to avoid problems with connection interruption. In this case, an option is to use the `nohup` command:

```bash
nohup bash reductionJypeT80S.sh 2016-09-08 2016-09-11 instr-t80cam.txt STRIPE82_0021 STRIPE82 use.email@gmail.com &> nohup_0021.out&
```

Note that here was used `&>` to redirect the `nohup` output to file `nohup_0021.out`, and the `&` was
used to indicate that the process must be executed in background. With the `nohup` command we avoid that the process terminate is the terminal, or the connection, is closed.

## The reduction Bot

The autonomous reduction mode is performed by `reductionbot80s.py`.
The program create a folder in the work directory to process some data and save the log files.

The `reductionbot80s.py` receive six parameter.

1. -u: The name of the current user
2. -e: The user e-mail
3. -t: Time interval, in hours, for the next reduction
4. -d: Time interval, in days, to search for Flat and Bias
5. -s: The hour that the bot start the reduction
6. -m: The minutes that the bot start the reduction


Also, it is recommended to run the bot as a background process:

```bash
nohup python reductionbott80s.py -u jype -e user.email@gmail.com -t 24 -d 20 -s 7 -m 0 &> nohup_bot&
```

The log files of bot is in the folder `reductionBotWDir/botLoggin`, in the current directory where the bot is running.
