#!/bin/bash
# This script mv the current campaign datas (pictures info CSV files, full tracks and logs)
# Data are moved to data/campaigns/campaignName/*

SCRIPT_DIR=$(cd `dirname $0` && pwd)

if [ $# -eq 0 ]
 then
   echo "Need to be called with the campaign name as argument (without special char plz)."
   exit 1
fi

CAMP_NAME=$1
CAMP_DIR="$SCRIPT_DIR/data/campaigns/$CAMP_NAME/"

mkdir -p $CAMP_DIR
cd $SCRIPT_DIR

mv picturesInfo.csv $CAMP_DIR
mv picturesInfo_secondaryGPS.csv $CAMP_DIR
mv track_full_main $CAMP_DIR
mv track_full_secondary $CAMP_DIR
mv opv.log $CAMP_DIR

echo "All files moved to $CAMP_DIR"

exit 0
