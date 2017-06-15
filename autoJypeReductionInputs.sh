#!/bin/bash
# Script with the recipie of reduction process.
# Created by Eduardo S. Pereira
# pereira.somoza@gmail.com

if [ $1 == '-h' ]; then
    echo ""
    echo ""
    echo "The input seq. is:"
    echo "star date yyyy-mm-dd, end date yyyy-mm-dd, inst. conf, tile, filed, red. folder name"
    echo ""
    echo ""
    echo "ex:"
    echo "autoJypeReductionInputs.sh 2016-09-08 2016-09-11 instr-t80cam.txt 0021 STRIPE82 STRIPE82_0058"
    echo ""
    exit
fi

yyyy=''
mm=''
dd=''

function splitDate(){
    a=(`echo $1 |sed 's/-/\n/g'`)
    yyyy=${a[0]}
    mm=${a[1]}
    dd=${a[2]}
}

echo "Automatic reduction process"
echo "for T80s project, using jype."
echo ""
echo "Written by: E. S. Pereira."
echo ""

sDate=$1
eDate=$2

#Name of file with instrument info.
inst=$3


tile=$4
field=$5

#Name of the folder that the pipeline will be save the reduced data
cName=$6

#Send Message when the process is finished
mailTo=$7

#Starting reduction Date
splitDate $sDate
yyyy0=$yyyy
mm0=$mm
dd0=$dd


#End reduction Date.
splitDate $eDate
yyyy1=$yyyy
mm1=$mm
dd1=$dd

#Number of parallel process to reduce individual images
nprR=3


ei=e
un=_
vcf=0

function parallelMasterFlat(){
    # Warning: The pipelie has a large space complexity,
    # max recomeded three filters.
    local filters=($1 $2 $3)
    for filt in "${filters[@]}";
    do
          echo ''
          echo ''
          echo ''
          echo "Starting the creation of master sky-flat for filter $filt."
          echo ''
          echo ''
          runcf.py  -s $sDate -e $eDate  -t 16 --instconfig $inst -f $filt &
          echo ''
          echo ''
          echo ''
    done
    wait

}

echo ""
echo "Invalidating all previous master frame."
jsubmitsql.py "update t80cftab set is_valid=1 where is_valid=0"
echo ""
echo "Creating and validating the Master Bias"
echo "Starting..."

runcf.py  -s $sDate -e $eDate -t 4 --instconfig $inst
validateCF.py j02-BIAS-b$yyyy0$mm0$dd0$ei$mm1$dd1-00-$cName $vcf

echo ""
echo "Creating the Master Sky-Flat, and, performing the reduction"
echo "of individual images for the field $field$un$tile."

echo ""

parallelMasterFlat R I G
parallelMasterFlat F660 U z
parallelMasterFlat F378 F395 F410
parallelMasterFlat F861 F515 F430

filters=(R I G F660 U z F378 F395 F410 F861 F515 F430)

for filt in "${filters[@]}";
do
    echo "Starting the reduction of individual images"
    echo "for filter $filt and field $field$un$tile."
    validateCF.py j02-FLAS-b$yyyy0$mm0$dd0$ei$mm1$dd1-$filt-00-$cName $vcf
    jgetlist.py -t SCIE -f $filt --addcond "Object like '%$tile%'" |xargs -I ARG -P $nprR runcosmet.py -o -u ARG
    jgetlist.py -t SCIE -f $filt --addcond "Object like '%$tile%'" |xargs -I ARG -P $nprR runcosmet.py  ARG
    echo ''
    echo ''
done

echo ''
echo ''
echo "Staring the combination of images by filter"
for filt in "${filters[@]}";
do
    echo ''
    echo ''
    echo "Combining images for  $field$un$tile  in filter $filt"
    echo ''
    echo ''
    echo ''
    runcoadding.py -u -o $field$un$tile $filt
done
wait


if [ $mailTo != '']; then
    export REPLYTO=jype@jype.com
    now=$(date +"%T")
    echo "The reducion process for $field$un$tile was finished at $now." | \
    mail -a From:jype@jype.com -s "noReply:Reduction for $field$un$tile finished" $mailTo
fi

echo "Reduction finished..."
