#!/bin/bash
# Script with the recipie of reduction process.
# Created by Eduardo S. Pereira
# pereira.somoza@gmail.com


echo "Automatic reduction process"
echo "for T80s project, using jype."
echo ""
echo "Written by: E. S. Pereira."
echo ""

#Number of parallel process to reduce individual images
nprR=3

#Starting reduction Date
yyyy0=2016
mm0=09
dd0=06

#End reduction Date.
yyyy1=2016
mm1=09
dd1=11

#Name of file with instrument info.
inst=instr-t80cam.txt

tile=0021
field=STRIPE82

#Name of the folder that the pipeline will be save the reduced data
cName=STRIPE82_0058

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
          echo "Starting the creationg of master sky-flat  "
          echo "for filter $filt."
          echo ''
          echo ''
          runcf.py  -s $yyyy0-$mm0-$dd0 -e $yyyy1-$mm1-$dd1  -t 16 --instconfig $inst -f $filt &
          echo ''
          echo ''
          echo ''
    done
    wait

}


filters=(R I G F660 U z F378 F395 F410 F861 F515 F430)

echo ""
echo "Invalidating all previous master frame."
jsubmitsql.py "update t80cftab set is_valid=1 where is_valid=0"
echo ""
echo "Creating and validating the Master Bias"
echo "Starting..."

runcf.py  -s $yyyy0-$mm0-$dd0 -e $yyyy1-$mm1-$dd1 -t 4 --instconfig $inst
validateCF.py j02-BIAS-b$yyyy0$mm0$dd0$ei$mm1$dd1-00-$cName $vcf

echo ""
echo "Creating the Master Sky-Flat, and, performing the reduction"
echo "of individual images for the field $field$un$tile."
echo ""


parallelMasterFlat R I G
parallelMasterFlat F660 U z
parallelMasterFlat F378 F395 F410
parallelMasterFlat F861 F515 F430


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

echo "Reduction finished..."
