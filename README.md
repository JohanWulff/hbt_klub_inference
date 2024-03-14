# hbt_klub_inference

## Setup

to be executed on lxplus9 
```
export SCRAM_ARCH="el8_amd64_gcc12"
cmsrel CMSSW_14_0_0
cd CMSSW_14_0_0/src
cmsenv
git clone -b hbtresdnn git@github.com:JohanWulff/hbt_klub_inference.git
scram b -j 4
```

## Add existing predictions to KLUB files

TBA: location of predition files on lxplus/eos

###  1. Create submission dirs and .dag files.

```
cd hbt_klub_inference/add_branch
python3 write_dag_addBranch.py --submit_base ~/afs/submit_dir \
                               --skims_dir /eos/user/l/lportale/hhbbtautau/skims/SKIMS_UL17/ \
                               --pred_dir /eos/user/j/jowulff/res_HH/predictions/{model_name}/{year}
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


### test addBranch command itself:

```
addBranch -i /eos/user/j/jowulff/res_HH/test_skims/DNN/SKIM_ZZZ/output_0.root \
          -t /eos/user/j/jowulff/res_HH/test_skims/KLUB/SKIMS_UL17/SKIM_ZZZ/output_0.root \
          -n hbtresdnn \
          -m true
```
