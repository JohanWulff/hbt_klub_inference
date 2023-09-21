from glob import glob
import os
from argparse import ArgumentParser
from subprocess import Popen, PIPE
from pathlib2 import Path


def make_parser():
    parser = ArgumentParser(description="Submit predicting of LLR \
Samples")
    parser.add_argument("-s", "--submit_base", type=str, 
                        help="Base dir to submit from")
    parser.add_argument("-d", "--skims_dir", type=str, 
                        help="directory where KLUB skims are located. e.g.:\n\
/eos/user/l/lportale/hhbbtautau/skims/SKIMS_UL17")
    parser.add_argument("-o", "--output_dir" ,type=str,
                        help="Dir to write output files to")
    parser.add_argument("-m", "--model_name" ,type=str,
                        help="model name. bsp. parametrised_baseline")
    parser.add_argument("-p", "--parametrised" ,action="store_true",
                        help="set this flag if evaluating a param. model")
    parser.add_argument("-b", '--broken', type=str, default="", required=False,
                        help=".txt file with broken files.")
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


def parse_goodfile_txt(goodfile:Path,):
    skims_dir = goodfile.absolute().parent
    with open(goodfile) as gfile:
        gfiles = sorted([Path(line.rstrip()) for line in gfile])
        if len(gfiles) == 0:
            print(f"Found 0 files in {goodfile}. Globbing all .root files in skim dir.")
            # goodfiles.txt is empty: just glob all .root files in 
            # skims dir and hope they're good
            gfiles = sorted([i for i in skims_dir.glob("*.root")])
        else:
            # check if the paths have been updated
            if gfiles[0].parent != skims_dir:
                # if not stick the filename on the end of the provided path
                # and hope for the best
                gfiles = [skims_dir / i.name for i in gfiles]
    return [str(gfile) for gfile in gfiles]


def return_subfile(outdir, executable,):
    file_str = f"executable={executable}\n\
log                     = singularity.$(ClusterId).log\n\
error                   = singularity.$(ClusterId).$(ProcId).err\n\
output                  = singularity.$(ClusterId).$(ProcId).out\n\
\n\
should_transfer_files = YES\n\
MY.JobFlavour = \"espresso\"\n\
output_destination      = root://eosuser.cern.ch/{outdir}/\n\
MY.XRDCP_CREATE_DIR     = True\n\
MY.SingularityImage     = \"/cvmfs/unpacked.cern.ch/registry.hub.docker.com/jwulff/lumin_3.8:latest\"\n\
\n\
Arguments = $(FILES)\n\
queue"
# transfer_input_files    = root://eosuser.cern.ch//eos/user/j/jowulff/res_HH/hbt_resonant_evaluation/branchnames.py, root://eosuser.cern.ch//eos/user/j/jowulff/res_HH/hbt_resonant_evaluation/feature_calc.py,root://eosuser.cern.ch//eos/user/j/jowulff/res_HH/hbt_resonant_evaluation/features.py,root://eosuser.cern.ch//eos/user/j/jowulff/res_HH/hbt_resonant_evaluation/first_nn.py,root://eosuser.cern.ch//eos/user/j/jowulff/res_HH/hbt_resonant_evaluation/helpers.py\n\
    return file_str


def return_executable(pyscript, model_name, parametrised):
    function_call_str = f'python ${{EXE}} -f $1 -o ./ -m {model_name}'
    if parametrised:
        function_call_str += " -p"
    file_str = f'#!/usr/bin/bash\n\
EXE="{pyscript}"\n\
{function_call_str} || exit 1\n\
exit 0'
    return file_str


def main(submit_base_dir: str, 
         skims_dir: str,
         outdir: str,
         model_name: str,
         parametrised: bool,
         broken_files: str=""):
    # skims_dir=f"/eos/user/l/lportale/hhbbtautau/skims/SKIMS_UL{year}"
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
    checkmake_dir(outdir)

    if not broken_files=="":
        with open(broken_files) as f:
            broken_list = [line.rstrip() for line in f] 
    
    for i, sample_dir in enumerate(samples):
        sample_name = sample_dir.split("/")[-1]
        print(f"Creating submission dir and writing dag \
files for sample ({i+1}/{len(samples)})\r", end="")
        # data samples are channel-dependant
        if "Run" in sample_name:
            continue
        # create /eos outdir for the sample
        eos_sample_dir = outdir.rstrip("/")+f"/{sample_name}"
        if not os.path.exists(eos_sample_dir):
            os.mkdir(eos_sample_dir)
        submit_dir = submit_base_dir.rstrip("/")+f"/{sample_name}"
        if not os.path.exists(submit_dir):
            os.mkdir(submit_dir)
        submitfile = submit_dir+f"/{sample_name}.submit"
        dagfile = submit_dir+f"/{sample_name}.dag"
        afs_exe = submit_dir+f"/executable.sh"
        goodfile = sample_dir+"/goodfiles.txt"
        if not os.path.exists(goodfile):
            print(f"{sample_name} does not have a goodfile.txt at \
{sample_dir}")
            gfiles = glob(sample_dir+"/*.root")
        else:
            gfiles = parse_goodfile_txt(Path(goodfile))
        # filter files for broken files
        if not broken_files == "":
            gfiles = [file for file in gfiles if file not in broken_list]
        if not os.path.exists(dagfile):
            with open(dagfile, "x") as dfile:
                for file in gfiles:
                    jobid = file.split("/")[-1]
                    print(f"JOB {jobid} {submitfile}", file=dfile)
                    print(f'VARS {jobid} FILES="{file}"', file=dfile)
        else:
            print(f"\n {dagfile} already exists.. Not creating new one \n")
        outfiles = [i.split('/')[-1] for i in gfiles]

        if not os.path.exists(submitfile):
            submit_string = return_subfile(outdir=f"{outdir}/{sample_name}",
                                           executable=afs_exe,)
            with open(submitfile, "x") as subfile:
                print(submit_string, file=subfile)
        else:
            print(f"\n {submitfile} already exists.. Not creating new one \n")

        if not os.path.exists(afs_exe):
            pyscript = f"{os.path.abspath('./')}/evaluate_klub.py"
            with open(afs_exe, "w") as f:
                print(return_executable(pyscript, model_name, parametrised), file=f)
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
         outdir=args.output_dir,
         model_name=args.model_name,
         parametrised=args.parametrised,
         broken_files=args.broken)
