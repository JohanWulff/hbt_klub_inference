import uproot
import re
import hashlib

from typing import List, Union
from glob import glob
import os
from argparse import ArgumentParser
from subprocess import Popen, PIPE


def make_parser():
    parser = ArgumentParser(description="add predictions to KLUB HTauTauTree")
    parser.add_argument("--submit_base", required=True,
                        help="Base dir to submit from")
    parser.add_argument("--skims_dir", required=True,
                        help="KLUB skims dir. ")
    parser.add_argument("--pred_dir", required=True,
                        help="/eos dir where prediction files are stored")
    parser.add_argument("--model_name", required=False, default="hbtresdnn", type=str,
                        help="model name (default: 'hbtresdnn')")
    parser.add_argument("--masses", required=False, nargs="+", type=int, default=None,
                        help="masses to add branches for. Default is all 25.")
    parser.add_argument("--spins", required=False, nargs="+", type=int, default=None,
                        help="spins to add branches for. Default is 0 and 2.")
    parser.add_argument("--classes", required=False, nargs="+", type=str, default=None,
                        help="classes to add branches for. Default is tt, hh, dy.")
    parser.add_argument("--shapes", required=False, nargs="+", type=str, default=None,
                        help="shapes to add branches for. Default is tes, ees, jes.")
    parser.add_argument("--num_files", required=False, type=int,
                        help="How many files to add per job.")
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
MY.JobFlavour = \"longlunch\"\n\
MY.WantOS = \"el7\"\n\
\n\
Arguments = $(FILES)\n\
queue"
    return file_str


def return_executable(pred_dir, cmssw_dir, branchfile, model_name):
    env_str = f"cd {cmssw_dir} || exit 1\n\
cmsenv\n\
cd -"
    file_str = f'#!/usr/bin/bash\n\
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch\n\
source $VO_CMS_SW_DIR/cmsset_default.sh\n\
{env_str}\n\
for file in $@; do\n\
filepath=$file\n\
filename="${{filepath##*/}}"\n\
pred_file="{pred_dir}/$filename"\n\
echo "running: addBranch -i $pred_file -t $filepath --branches {branchfile} -n {model_name}"\n\
addBranch -i $pred_file -t $filepath --branches {branchfile} -n {model_name}|| exit 1\n\
done\n\
exit 0'
    return file_str


def match_branches(filename,
                   masses,
                   spins,
                   classes,
                   shapes,
                   treename="hbtres",
                   model_name="hbtresdnn"):
    """
    return a list of branches that match regex

    branches look like:
    {model_name}_mass[250-3000]_spin[0,2]_{hh,tt,dy} (nominal)
    {model_name}_mass[250-3000]_spin[0,2]_{hh,tt,dy}_{tes,ees,jes}_{up,down} (with shapes)
    """
    masses_str = "|".join(map(str, masses))
    spins_str = "|".join(map(str, spins))
    classes_str = "|".join(classes)
    shapes_str = "|".join(shapes)

    pattern = rf"{model_name}_mass({masses_str})_spin({spins_str})_({classes_str})(_({shapes_str})_(up|down))?"
    regex = re.compile(pattern)
    file = uproot.open(filename)
    branches = file[treename].keys()
    return [branch for branch in branches if regex.match(branch)]
    

def main(submit_base_dir: str,
            skims_dir: str, 
            pred_dir: str, 
            model_name: str,
            masses: Union[List[int],None],
            spins: Union[List[int],None],
            classes: Union[List[str],None], 
            shapes: Union[List[str],None], 
            num_files: 100,
            cmssw_dir: str=os.getcwd()):
    
    if masses is None:
        print("No masses given. Using default list (all 25).")
        masses = [250, 260, 270, 280, 300,
                  320, 350, 400, 450, 500,
                  550, 600, 650, 700, 750,
                  800, 850, 900, 1000, 1250,
                  1500, 1750, 2000, 2500, 3000]
    if spins is None:
        print("No spins given. Using 0 and 2.")
        spins = [0, 2]
    if classes is None:
        print("No classes given. Using tt, hh, dy.")
        classes = ["tt", "hh", "dy"]
    if shapes is None:
        print("No shapes given. Using tes, ees, jes.")
        shapes = ["tes", "ees", "jes"]

    # create a hash of the branches to add
    cache_key = [masses, spins, classes, shapes]
    cache_hash = hashlib.sha256(str(cache_key).encode("utf-8")).hexdigest()[:10]
    branchfile = f"./branches_{cache_hash}.txt"
    branchfile_is_cached = os.path.exists(branchfile)
    if branchfile_is_cached:
        print(f"Branches are cached. Using cached file: {branchfile}.")
    else:
        print(f"Caching branches to {branchfile}.")
        # open a file in the pred_dir to check which branches are available
        pred_file = glob(pred_dir+"/*/output_*.root")[0]
        matched_branches = match_branches(pred_file, masses, spins, classes, shapes)
        with open(branchfile, "w") as bfile:
            # write all matched branches to the bfile
            for branch in matched_branches:
                print(branch, file=bfile)

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
        filechunks = [files[i:i+num_files] for i in range(0, len(files), num_files)]
        if not os.path.exists(dagfile):
            with open(dagfile, "x") as dfile:
                for chunk in filechunks:
                    jobid = (chunk[0]).split("/")[-1]
                    print(f"JOB {jobid} {submitfile}", file=dfile)
                    print(f'VARS {jobid} FILES="{" ".join(chunk)}"', file=dfile)
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
                                               branchfile,
                                               model_name,)
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
        afs_branchfile = f"{submit_base_dir}/{sample_name}/{branchfile}"
        if not os.path.exists(afs_branchfile):
            os.system(f"cp {branchfile} {afs_branchfile}")


if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()
    main(submit_base_dir=args.submit_base,
         skims_dir=args.skims_dir,
         pred_dir=args.pred_dir,
         model_name=args.model_name,
         masses=args.masses,
         spins=args.spins,
         classes=args.classes,
         shapes=args.shapes,
         num_files=args.num_files)
