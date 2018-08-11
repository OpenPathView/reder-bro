#!/bin/bash 
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
cd $SCRIPTPATH
source .venv/opv/bin/activate
rederbro $*
