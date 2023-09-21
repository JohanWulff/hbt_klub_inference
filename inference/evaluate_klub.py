# coding: utf-8

from __future__ import annotations

import os
import tempfile
import shutil
from fnmatch import fnmatch
from multiprocessing import Pool as ProcessPool
from typing import Any
from argparse import ArgumentParser
from tqdm import tqdm

import awkward as ak
import numpy as np
import uproot

# load the nn evaluation
from first_nn import evaluate_events, evaluate_events_param, evaluate_events_mass_param, nn_columns
from feature_calc import spin2id

#
# configurations
#

masses = [
    250, 260, 270, 280, 300, 320, 350, 400, 450, 500, 550, 600, 650,
    700, 750, 800, 850, 900, 1000, 1250, 1500, 1750, 2000, 2500, 3000,
]
spins = [0, 1]

klub_index_cols = ["EventNumber", "RunNumber", "lumi"]
klub_cut_cols = ['isLeptrigger', "pairType", 'nleps', 'nbjetscand'] 

baseline_selection = (
    "isLeptrigger & "
    "((pairType == 0) | (pairType == 1) | (pairType == 2)) & "
    "(nleps == 0) & "
    "(nbjetscand > 1)"
)


def make_parser():
    parser = ArgumentParser(description=("Run DNN evaluation with a given model"
                                         "on a provided list of samples"))
    parser.add_argument("-i", "--skim_dir", type=str, required=False,
                        help="directory, where the skims are located")
    parser.add_argument("-o", "--out_dir", type=str, required=True,
                        help="output directory")
    parser.add_argument("-f", "--file_names", type=str, nargs="+", required=False,
                        help="file name(s). Use this argument if running with Condor.")
    parser.add_argument("--sample_name", type=str, required=False,
                        help="sample name")
    parser.add_argument("--sample_pattern", nargs="+", type=str, required=False,
                        help="sample pattern(s)")
    parser.add_argument("-m", "--model_name", type=str, required=True, default='nonparam_baseline',
                        help="Model name as provided in Readme (TODO)")
    parser.add_argument("-p", "--parametrised", action="store_true",
                        help="If set, evaluate parametrised model.")
    parser.add_argument("-n", "--n_parallel", type=int, default=1, 
                        help="number of cores to use in parallel. Default = 1")
    parser.add_argument("-g", "--use_gpu", action='store_true', help="If set, use gpu.")
    return parser
    

#
# high-level evaluation functions
#

def evaluate_samples(
    skim_directory: str,
    output_directory: str,
    model_name: str,
    sample_patterns: str | list[str] = "*",
    parametrised: bool=False,
    n_parallel: int = 1,
) -> None:
    # prepare patterns
    if not isinstance(sample_patterns, list):
        sample_patterns = [sample_patterns]

    # get a list of all sample names in the klub directory
    sample_names = []
    for sample_name in os.listdir(skim_directory):
        sample_dir = os.path.join(skim_directory, sample_name)
        if not os.path.isdir(sample_dir) or not os.path.exists(os.path.join(sample_dir, "output_0.root")):
            continue
        # check pattern
        if not any(fnmatch(sample_name, p) or fnmatch(sample_name, "SKIM_" + p) for p in sample_patterns):
            continue
        sample_names.append(sample_name)

    # start the evaluation
    print(f"evaluating {len(sample_names)} samples")
    for sample_name in sample_names:
        evaluate_sample(skim_directory, output_directory, sample_name, model_name, parametrised, n_parallel=n_parallel)


def evaluate_sample(
    skim_directory: str,
    output_directory: str,
    sample_name: str,
    model_name: str,
    parametrised: bool,
    n_parallel: int = 1,
) -> None:
    print(f"evaluate {sample_name} ...")

    # ensure that the output directory exists
    output_sample_dir = os.path.join(output_directory, sample_name)
    output_sample_dir = os.path.expandvars(os.path.expanduser(output_sample_dir))
    if not os.path.exists(output_sample_dir):
        os.makedirs(output_sample_dir)

    # determine all file names to load
    input_sample_dir = os.path.join(skim_directory, sample_name)
    evaluation_args = [
        (os.path.join(input_sample_dir, file_name), os.path.join(output_sample_dir, file_name), model_name, parametrised)
        for file_name in os.listdir(input_sample_dir)
        if fnmatch(file_name, "output_*.root")
    ]

    # potentially run in parallel
    if n_parallel > 1:
        with ProcessPool(n_parallel) as pool:
            list(tqdm(
                pool.imap(_evaluate_file_mp, evaluation_args),
                total=len(evaluation_args),
            ))
    else:
        list(tqdm(
            map(_evaluate_file_mp, evaluation_args),
            total=len(evaluation_args),
        ))
    print("done")


def evaluate_file_condor(input_file_path: str, output_path: str, model_name: str, parametrised: bool) -> None:
    # prepare expressions
    expressions = list(set(klub_index_cols) | set(nn_columns))
    # get the bool mask
    with uproot.open(input_file_path) as f:
        cut_arr = f["HTauTauTree"].arrays(expressions=list(set(klub_cut_cols) | set(klub_index_cols)))
    baseline_mask = (cut_arr.isLeptrigger == 1) & ((cut_arr.pairType == 0) | (cut_arr.pairType == 1) | (cut_arr.pairType == 2)) & (cut_arr.nleps == 0) & (cut_arr.nbjetscand > 1)
    # load the klub array
    with uproot.open(input_file_path) as f:
        input_array = f["HTauTauTree"].arrays(expressions=expressions, cut=baseline_selection)
    # run the evaluation
    if parametrised == True:
        # check if this is a signal file
        if "_ggF_" in input_file_path or "_VBF_" in input_file_path:
            sample_name = input_file_path.split('/')[-2]
            # sample_name will be something like SKIM_VBF_BulkGraviton_m2000
            # read mass and spin
            mass = int(sample_name.split("_")[-1][1:])
            spin = (sample_name.split("_")[-2].replace("Bulk", "")).lower()
            # run param eval just for the mass and spin of this sample
            # output_array = evaluate_events_mass_param(input_array, [mass], [spin2id[spin]], model_name=model_name)
            output_array = evaluate_events_param(input_array, [mass], [spin2id[spin]], model_name=model_name)
            # output_array = evaluate_events_mass_param(input_array, [mass], model_name=model_name)
        else:
            output_array = evaluate_events_param(input_array, masses, spins, model_name=model_name)
            # output_array = evaluate_events_mass_param(input_array, masses, model_name=model_name)
    else:
        output_array = evaluate_events(input_array, model_name=model_name)

    # set prediction to -1 for all events not passing baseline selection
    index_arr = cut_arr[klub_index_cols]
    for field in output_array.fields:
        new_array = (-1*np.ones(len(baseline_mask)))
        new_array[baseline_mask] = output_array[field]
        out_arr = ak.with_field(index_arr, new_array, field)
    # save the output as root
    # since we're using condor and the xrootd file transfer, 
    # we only need to write to the cwd
    # and then condor transfers to eos for us
    output_file_name = "/".join([output_path,input_file_path.split("/")[-1]])
    def write(path):
        with uproot.recreate(path) as output_file:
            output_file["evaluation"] = dict(zip(out_arr.fields, ak.unzip(out_arr)))
    write(output_file_name)


def evaluate_files(input_files: list, output_path: str, model_name:str, parametrised: bool) -> None:
    for file in input_files:
        evaluate_file_condor(input_file_path=file,
                             output_path=output_path,
                             model_name=model_name,
                             parametrised=parametrised)
    print("done")


def evaluate_file(input_file_path: str, output_file_path: str, model_name: str, parametrised: bool) -> None:

    # prepare expressions
    expressions = list(set(klub_index_cols) | set(nn_columns))

    # load the klub array
    with uproot.open(input_file_path) as f:
        input_array = f["HTauTauTree"].arrays(expressions=expressions, cut=baseline_selection)

    # run the evaluation
    if parametrised == True:
        # check if this is a signal file
        if "_ggF_" in input_file_path or "_VBF_" in input_file_path:
            sample_name = input_file_path.split('/')[-2]
            # sample_name will be something like SKIM_VBF_BulkGraviton_m2000
            # read mass and spin
            mass = int(sample_name.split("_")[-1][1:])
            spin = (sample_name.split("_")[-2].replace("Bulk", "")).lower()
            # run param eval just for the mass and spin of this sample
            # output_array = evaluate_events_mass_param(input_array, [mass], [spin2id[spin]], model_name=model_name)
            output_array = evaluate_events_param(input_array, [mass], [spin2id[spin]], model_name=model_name)
            # output_array = evaluate_events_mass_param(input_array, [mass], model_name=model_name)
        else:
            output_array = evaluate_events_param(input_array, masses, spins, model_name=model_name)
            # output_array = evaluate_events_mass_param(input_array, masses, model_name=model_name)
    else:
        output_array = evaluate_events(input_array, model_name=model_name)

    # add index columns
    for c in klub_index_cols:
        output_array = ak.with_field(output_array, input_array[c], c)

    # save the output as root
    # note: since /eos does not like write streams, first write to a tmp file and then copy
    def write(path):
        output_file = uproot.recreate(path)
        output_file["evaluation"] = dict(zip(output_array.fields, ak.unzip(output_array)))

    with tempfile.NamedTemporaryFile(suffix=".root") as tmp:
        write(tmp.name)
        shutil.copy2(tmp.name, output_file_path)


def _evaluate_file_mp(args: Any) -> None:
    return evaluate_file(*args)


# entry hook
if __name__ == "__main__":

    parser = make_parser()
    args = parser.parse_args()
    if args.use_gpu:
        import torch
        try:
            torch.cuda.set_device(0)
            print("Using GPU:")
            print(torch.cuda.get_device_name())
        except:
            print("couldn't access GPU")


    if args.sample_name:
        evaluate_sample(skim_directory=args.skim_dir,
                        output_directory=args.out_dir,
                        model_name=args.model_name,
                        sample_name=args.sample_name,
                        parametrised=args.parametrised,
                        n_parallel=args.n_parallel)
    elif args.sample_pattern:
        evaluate_samples(skim_directory=args.skim_dir,
                         output_directory=args.out_dir,
                         sample_patterns=args.sample_pattern,
                         model_name=args.model_name,
                         parametrised=args.parametrised,
                         n_parallel=args.n_parallel)
    elif args.file_names:
        evaluate_files(input_files=args.file_names,
                             output_path=args.out_dir,
                             model_name=args.model_name,
                             parametrised=args.parametrised
        )
    else:
        raise ValueError("Either --sample_name or --sample_pattern must be specified")
    
    #evaluate_samples(
    #    skim_directory="/eos/user/t/tokramer/hhbbtautau/skims/2017",
    #    output_directory="/eos/user/m/mrieger/hhres_dnn_datacards/nn/2017/param_test",
    #    # all samples divided into logical groups
    #    # sample_patterns=["ggF_*_m*"],
    #    # sample_patterns=["VBF_*_m*"],
    #    # sample_patterns=["TT_*"],
    #    # sample_patterns=["ST_*"],
    #    # sample_patterns=["DY_amc_PtZ_*"],
    #    # sample_patterns=["WJets_*", "EWK*"],
    #    # sample_patterns=["WW", "WZ", "ZZ", "WWW", "WWZ", "WZZ", "ZZZ"],
    #    # sample_patterns=["TTWJets*", "TTZTo*", "TTWW", "TTWZ", "TTZZ"],
    #    # sample_patterns=["GluGluHToTauTau", "VBFHToTauTau", "ZHToTauTau", "WminusHToTauTau", "WplusHToTauTau", "ttHTobb", "ttHToTauTau"],  # noqa
    #    # single samples for reprocessing
    #    sample_patterns=["WJets_HT2500ToInf"],
    #    n_parallel=1,
    #)

    #evaluate_sample(
    #     skim_directory="/eos/user/t/tokramer/hhbbtautau/skims/2017",
    #     output_directory="/eos/user/j/jowulff/hhres_dnn_datacards/nn/2017",
    #     sample_name="SKIM_ggF_Radion_m900",
    #     n_parallel=4,
    #)

    # sample_patterns = ggF_*_m*
    # sample_patterns = VBF_*_m*
    # sample_patterns = TT_*
    # sample_patterns = ST_*
    # sample_patterns = DY_amc_PtZ_*
    # sample_patterns = WJets_* EWK*
    # sample_patterns = WW WZ ZZ WWW WWZ WZZ ZZZ
    # sample_patterns = TTWJets* TTZTo* TTWW TTWZ TTZZ
    # sample_patterns = GluGluHToTauTau VBFHToTauTau ZHToTauTau WminusHToTauTau WplusHToTauTau ttHTobb ttHToTauTau  #noqa
