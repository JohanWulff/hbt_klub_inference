import json
from glob import glob
import os
from argparse import ArgumentParser
from subprocess import Popen, PIPE


def make_parser():
    parser = ArgumentParser(description="Submit predicting of LLR \
Samples")
    parser.add_argument("-s", "--submit_base", type=str, 
                        help="Base dir to submit from")
    parser.add_argument("-d", "--skims_dir", type=str, 
                        help="KLUB skims dir. ")
    parser.add_argument("-o", "--pred_dir", type=str, 
                        help="outdir where the predictions were stored.")
    parser.add_argument("-m", "--model_name" ,type=str,
                        help="model name. ex: parametrised_baseline")
    parser.add_argument("-p", "--parametrised" ,action="store_true",
                        help="set this flag if evaluating a param. model")
    return parser
                            

def checkmake_dir(path):
    if not os.path.exists(path):
        print(f"{path} does not exist.")
        print("Shall I create it now?")
        yn = input("[y/n] ?")
        if yn.strip().lower() == 'y':
            print('Creating dir(s)!')
            os.makedirs(path)
        else:
            raise ValueError(f"{path} does not exist")


def return_subfile():
    file_str = f"executable=executable.sh\n\
log                     = $(ClusterId).log\n\
error                   = $(ClusterId).$(ProcId).err\n\
output                  = $(ClusterId).$(ProcId).out\n\
\n\
MY.JobFlavour = \"espresso\"\n\
\n\
Arguments = $(FILES)\n\
queue"
    return file_str


def return_executable(pred_dir, cmssw_dir, model_name, parametrised):
    env_str = f"cd {cmssw_dir} || exit 1\n\
cmsenv\n\
cd -"
    file_str = f'#!/usr/bin/bash\n\
{env_str}\n\
filepath=$1\n\
filename="${{filepath##*/}}"\n\
pred_file="{pred_dir}/$filename"\n\
echo "running: addBranch -i $pred_file -t $filepath -n {model_name} -p {str(parametrised).lower()}"\n\
addBranch -i $pred_file -t $filepath -n {model_name} -p {str(parametrised).lower()} || exit 1\n\
exit 0'
    return file_str


def main(submit_base_dir: str,
         skims_dir: str, 
         pred_dir: str, 
         model_name: str,
         parametrised: bool,
         cmssw_dir: str=os.getcwd()):
    # skims_dir=f"/eos/user/j/jowulff/res_HH/KLUB_skims/SKIMS_UL{year}"
    # pred_dir=f"/eos/user/j/jowulff/res_HH/Condor_out/predictions_individual/20{year}/{model_name}"
    # check if it starts with /afs
    print(f"checking for files in {skims_dir}")
    samples = glob(skims_dir+"/SKIM_*")
    if len(samples) == 0:
        print(f"Found {len(samples)} samples")
        print(f"globbing all dirs in {skims_dir}")
        samples = glob(skims_dir+"/*")
        print(f"Found {len(samples)} samples")


    if not submit_base_dir.startswith("/afs"):
        raise ValueError("Submission must happen from /afs!")
    checkmake_dir(submit_base_dir)
    # copy executables to /afs. Condor cannot access /eos at the time of writing
    for i, sample_dir in enumerate(samples):
        sample_name = sample_dir.split("/")[-1]
        print(f"Creating submission dir and writing dag \
files for sample ({i+1}/{len(samples)})\r", end="")
        # data samples are channel-dependant
        if "Run" in sample_name:
            continue
        # create /eos outdir for the sample
        submit_dir = submit_base_dir.rstrip("/")+f"/{sample_name}"
        if not os.path.exists(submit_dir):
            os.mkdir(submit_dir)
        submitfile = submit_dir+f"/{sample_name}.submit"
        dagfile = submit_dir+f"/{sample_name}.dag"
        submit_string = return_subfile()
        #if not broken_files == "":
            #broken_list = 
        files = glob(f"{sample_dir}/*.root")
        if not os.path.exists(dagfile):
            with open(dagfile, "x") as dfile:
                for file in files:
                    jobid = file.split("/")[-1]
                    print(f"JOB {jobid} {submitfile}", file=dfile)
                    print(f'VARS {jobid} FILES="{file}"', file=dfile)
        else:
            print(f"\n {dagfile} already exists.. Not creating new one \n")
        if not os.path.exists(submitfile):
            with open(submitfile, "x") as subfile:
                print(submit_string, file=subfile)
        else:
            print(f"\n {submitfile} already exists.. Not creating new one \n")
        afs_exe = f"{submit_base_dir}/{sample_name}/executable.sh"
        if not os.path.exists(afs_exe):
            executable_str = return_executable(f"{pred_dir}/{sample_name}",
                                               cmssw_dir,
                                               model_name,
                                               parametrised)
            with open(afs_exe, "x") as exe:
                print(executable_str, file=exe)
            prcs = Popen(f"chmod 744 {afs_exe}",shell=True, 
                        stdin=PIPE, stdout=PIPE, encoding='utf-8')
            out, err = prcs.communicate()
            if err:
                print(err)
                raise ValueError(f"Unable to chmod {afs_exe} to 744")
        else:
            print(f"\n {afs_exe} already exists.. Not creating new one \n")
if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    main(submit_base_dir=args.submit_base,
         skims_dir=args.skims_dir,
         pred_dir=args.pred_dir,
         model_name=args.model_name,
         parametrised=args.parametrised)
