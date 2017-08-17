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


# Run jype

These commands will activate the Jype environment in a Conda environment:


```bash
source activate jypeenv
or
source /path/to/miniconda/bin/activate jypeenv
```
