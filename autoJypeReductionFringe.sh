#!/bin/bash
# Script with the recipie of reduction process.
# Created by Eduardo S. Pereira
# pereira.somoza@gmail.com


echo "Automatic reduction process, specific for fringe."
echo "for T80s project, using jype."
echo ""
echo "Written by: E. S. Pereira."
echo ""


nprocess=1
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

tile=0058
cNname=0021
field=STRIPE82

ei=e
un=_
vcf=0

filters=(z)

for filt in "${filters[@]}";
do
    echo ''
    echo "Starting the creation of  the master fringe for $filt filter."
    echo ''
    echo ''
    runcf.py -o -u -s $yyyy0-$mm0-$dd0 -e $yyyy1-$mm1-$dd1  -t 64 --instconfig $inst -f $filt
    validateCF.py j02-FRIN-b$yyyy0$mm0$dd0$ei$mm1$dd1-z-00-$field$un$tile $vcf
done


for filt in "${filters[@]}";
do
    echo "Starting the reduction of individual images"
    echo "for filter $filt and field $field$un$cNname"
    jgetlist.py -t SCIE -f $filt --addcond "Object like '%$cNname%'" |xargs -I ARG -P $nprR runcosmet.py -o -u ARG
    jgetlist.py -t SCIE -f $filt --addcond "Object like '%$cNname%'" |xargs -I ARG -P $nprR runcosmet.py  ARG
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
    echo "Combining images for  $field$un$cNname  in filter $filt"
    echo ''
    echo ''
    echo ''
    runcoadding.py -u -o $field$un$cNname $filt

done
wait

echo "Reduction finished..."
