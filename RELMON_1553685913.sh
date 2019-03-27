#!/bin/bash
DIR=$(pwd)
git clone https://github.com/justinasr/relmonservice2.git
scramv1 project CMSSW CMSSW_10_4_0
cd CMSSW_10_4_0/src
eval `scramv1 runtime -sh`
cd $DIR
mkdir -p Reports
python3 relmonservice2/remote_apparatus.py --config 1553685913.json --cert user.crt.pem --key user.key.pem
rm *.root
tar -zcvf 1553685913.tar.gz Reports