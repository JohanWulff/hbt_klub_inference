# hbt_klub_inference

## Setup

to be executed on lxplus. 

```
export SCRAM_ARCH="slc7_amd64_gcc820"
cmsrel CMSSW_12_2_4
cd CMSSW_12_2_4/src
cmsenv
git clone -b hbtresdnn git@github.com:JohanWulff/hbt_klub_inference.git
scram b -j 4
```

## Add existing predictions to KLUB files

TBA: location of predition files on lxplus/eos

###  1. Create submission dirs and .dag files.

```
cd hbt_klub_inference/add_branch
python3 write_dag_addBranch.py -s ~/afs/submit_dir \
                               -d /eos/user/l/lportale/hhbbtautau/skims/SKIMS_UL17/ \
                               -o /eos/user/j/jowulff/res_HH/predictions/{model_name}/{year} \
                               -m model_name
```

### 2. Submit!

```
cd ~/afs/submit/dir
for dir in $(find . -mindepth 1 -maxdepth 1 -type d); do cd $dir ; condor_submit_dag *.dag; cd -; done
```

rescue in case of failed jobs

```
for dir in $(find . -mindepth 1 -maxdepth 1 -type d); do resc=$(find $dir -type f -name "*rescue001"); if [ ! -z $resc ]; then cd $dir ; condor_submit_dag *.dag; cd -; fi ; done
```

change 001 to 002 for a second round if necessary.
