# Pipeline Instalation Process


## miniconda


The first step is install the miniconda environment

```bash
cd <install_directory_here>
wget -N https://archive.cefca.es/conda/bin/bootstrap.sh && chmod +rx bootstrap.sh && ./bootstrap.sh && rm -f ./bootstrap.sh
```

And include the miniconda to your environment `PATH`

```bash
export PATH="${PWD}/miniconda/bin:${PATH}"
```

## Jype Instalation

To install Jype it is necessary to have the access to the j-pas conda channel (see <http://www.j-pas.org/wiki/index.php/Conda_jype>).  In this page <https://j-pas.org/admin/adminuser/condaaccess> you can get the link to conda's temporary channel for jype. You have to save the link provided there and use it in the following commands instead of AUTHCHANNEL. The following conda command searches in this channel, and packages are automatically downloaded.


Using the AUTHCHANNEL from CEFCA, now it is possible to install the pipeline:

```bash
conda create --name jypeenv --channel AUTHCHANNEL python=2.7 numpy=1.12 jype=0.9.1
```


## Run jype

These commands will activate the Jype environment in a Conda environment:


```bash
source activate jypeenv
or
source /path/to/miniconda/bin/activate jypeenv
```

## Jype Data Base

The first step is generate the database for the set of image that will be reduced.

1 - Start mysql with (In the jype virtual machine at t80)

```bash
cd /home/jype/jype
```

Edit the file jpas.sql, in line 90 change the name of database for the new reduction, e.g.,

```sql
 DROP DATABASE IF EXISTS `MY_DATA_BASE`;
 CREATE DATABASE `MY_DATA_BASE`;
 USE `MY_DATA_BASE`;


 DROP DATABASE IF EXISTS `STRIPE82_0044`;
 CREATE DATABASE `STRIPE82_0044`;
 USE `STRIPE82_0044`;
```

Open mysql with the command
```bash
mysql -u jypesql -p
```


Inside mysql run the command

```sql
source jpas.sql;
```

Now change to the database that you created
```sql
use 'STRIPE82_0044';
```

Now, update the filters with the command;

```sql
load data local infile 't80s.filters' into table filter;
```

Close mysql;
```sql
quit;
```

It is necessary complete some informations in the database, in this case, open a web browser and type

<http://192.168.20.101/phpmyadmin/>

The  user and password are the same used in mysql terminal mode.

Select the database that you created in the previous step and select the table ccdchip.

Complete the field XSize, YSize, PixelScale and Channel for e2v CCD290-99 with the following information, respectively: 9216, 9232, 0.555, 16.

Also verify if all the filters was correctly insert into the table filter.


The next step  it is the inserting of the tile info in the database.
In this case, create a txt (e.g, tiles.txt) file with the following informations:

'''
# 1 PNAME
# 2 RA
# 3 DEC
# 4 RADECsys_ID
# 5 PIXEL_SCALE
# 6 IMAGE_SIZE
STRIPE82_0099  308.97671 -0.69992 1 0.550 10000
'''

The last line has the name of the tile, that will be used to combine the images.

Now start the conda env with the jype version (the more stable is the 0.9)

```bash
source miniconda/bin/activate jypeenv
```

With this env activated, we insert the tiles info with the command
```bash
inserttiles.py tiles.txt
```
