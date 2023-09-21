# coding: utf-8

from __future__ import annotations

from typing import List

import numpy as np
import awkward as ak

from branchnames import *  # noqa
from feature_calc import *  # noqa
from features import feats 

from lumin.nn.ensemble.ensemble import Ensemble
from lumin.nn.callbacks.data_callbacks import ParametrisedPrediction


def preprocess_mass(m, cont_feats, pipe):
    idx = cont_feats.index('res_mass')
    m -= pipe[0].mean_[idx]
    m /= pipe[0].scale_[idx]
    return m

#
# NN evaluation
#

masses = [
    250, 260, 270, 280, 300, 320, 350, 400, 450, 500, 550, 600, 650,
    700, 750, 800, 850, 900, 1000, 1250, 1500, 1750, 2000, 2500, 3000,
]
spins = [0, 1]


def evaluate_events(events: ak.Array,
                    mass: int=250,
                    spin: int=0,
                    year: int=2017,
                    model_name = "nonparam_baseline") -> ak.Array:
    ensembles = [('/eos/user/j/jowulff/res_HH'
                 f'/cms_runII_dnn_resonant/{model_name}'
                 f'/weights/selected_set_0_{model_name}'),
                 ('/eos/user/j/jowulff/res_HH'
                 f'/cms_runII_dnn_resonant/{model_name}'
                 f'/weights/selected_set_1_{model_name}')]
    input_pipes = [('/eos/user/j/jowulff/res_HH'
                   f'/cms_runII_dnn_resonant/{model_name}'
                   f'/weights/selected_set_0_{model_name}_input_pipe.pkl'),
                    ('/eos/user/j/jowulff/res_HH'
                   f'/cms_runII_dnn_resonant/{model_name}'
                   f'/weights/selected_set_1_{model_name}_input_pipe.pkl')]
    events = calc_feats(events,mass=mass, spin=spin, year=year)

    cont_feats = feats[model_name][0] 
    cat_feats = feats[model_name][1] 

    X_0, X_1 = prepare_feats(events, cont_feats, cat_feats, input_pipes)
    ensemble_0 = Ensemble.from_save(ensembles[0])
    ensemble_1 = Ensemble.from_save(ensembles[1])

    events['pred'] = np.zeros(len(events))
    np_preds = events['pred'].to_numpy()
    # predict on opposite halves
    np_preds[events.EventNumber % 2 == 0] = ak.flatten(ensemble_1.predict(X_0)).to_numpy()
    np_preds[events.EventNumber % 2 == 1] = ak.flatten(ensemble_0.predict(X_1)).to_numpy()
    return ak.zip({f"dnn_{model_name}": events['pred']})


def evaluate_events_param(events: ak.Array,
                    masses: list = masses,
                    spins: list = spins,
                    year: int=2017,
                    model_name: str = "param_baseline",) -> ak.Array:

    ensembles = [('/eos/user/j/jowulff/res_HH'
                 f'/cms_runII_dnn_resonant/{model_name}'
                 f'/weights/selected_set_0_{model_name}'),
                 ('/eos/user/j/jowulff/res_HH'
                 f'/cms_runII_dnn_resonant/{model_name}'
                 f'/weights/selected_set_1_{model_name}')]
    input_pipes = [('/eos/user/j/jowulff/res_HH'
                   f'/cms_runII_dnn_resonant/{model_name}'
                   f'/weights/selected_set_0_{model_name}_input_pipe.pkl'),
                    ('/eos/user/j/jowulff/res_HH'
                   f'/cms_runII_dnn_resonant/{model_name}'
                   f'/weights/selected_set_1_{model_name}_input_pipe.pkl')]
    # copy potential singletons
    masses = list(masses)
    spins = list(spins)

    cont_feats = feats[model_name][0] 
    cat_feats = feats[model_name][1] 

    events = calc_feats(events, mass=masses[0], spin=spins[0], year=year)  # THIS CURRENTLY BREAKS
    X_0, X_1 = prepare_feats(events, cont_feats, cat_feats, input_pipes)
    ensemble_0 = Ensemble.from_save(ensembles[0])
    ensemble_1 = Ensemble.from_save(ensembles[1])
    input_pipe_0 = load_input_pipe(input_pipes[0])
    input_pipe_1 = load_input_pipe(input_pipes[1])

    train_feats = cont_feats + cat_feats
    pred_names = []
    for m in masses:
        for s in spins:
            pred_name = f"dnn_{model_name}_spin{id2val[s]}_mass{m}"
            pred_names.append(pred_name)
            events = ak.with_field(events, np.zeros(len(events), dtype=float), pred_name)
            np_preds = np.asarray(events[pred_name])

            for e, X, pipe, assign_mask in [
                (ensemble_0, X_1, input_pipe_0, (events.EventNumber % 2 == 1)),
                (ensemble_1, X_0, input_pipe_1, (events.EventNumber % 2 == 0)),
            ]:
                # predict
                mass_param = ParametrisedPrediction(
                    train_feats,
                    ['res_mass', 'spin'],
                    [preprocess_mass(m, cont_feats, pipe), s],
                )
                preds = e.predict(X, cbs=[mass_param], verbose=False)
                # assign
                np_preds[assign_mask] = np.asarray(ak.flatten(preds))

    return ak.zip({pred_name: events[pred_name] for pred_name in pred_names})


def evaluate_events_mass_param(events: ak.Array,
                    masses: list = masses,
                    year: int=2017,
                    model_name: str = "param_baseline",) -> ak.Array:
    '''
    This function is used to evaluate the half-parametrised version i made, when i 
    accidentally forgot to include the spin in the parametrisation. 
    Let's see how much difference it makes.
    '''
    ensembles = [('/eos/user/j/jowulff/res_HH'
                 f'/cms_runII_dnn_resonant/{model_name}'
                 f'/weights/selected_set_0_{model_name}'),
                 ('/eos/user/j/jowulff/res_HH'
                 f'/cms_runII_dnn_resonant/{model_name}'
                 f'/weights/selected_set_1_{model_name}')]
    input_pipes = [('/eos/user/j/jowulff/res_HH'
                   f'/cms_runII_dnn_resonant/{model_name}'
                   f'/weights/selected_set_0_{model_name}_input_pipe.pkl'),
                    ('/eos/user/j/jowulff/res_HH'
                   f'/cms_runII_dnn_resonant/{model_name}'
                   f'/weights/selected_set_1_{model_name}_input_pipe.pkl')]
    # copy potential singletons
    masses = list(masses)

    cont_feats = feats[model_name][0] 
    cat_feats = feats[model_name][1] 

    # not parametrised in spin and spin not part of input feats so just use 0
    events = calc_feats(events, mass=masses[0], spin=0, year=year) 
    #from IPython import embed
    #embed()
    X_0, X_1 = prepare_feats(events, cont_feats, cat_feats, input_pipes)
    ensemble_0 = Ensemble.from_save(ensembles[0])
    ensemble_1 = Ensemble.from_save(ensembles[1])
    input_pipe_0 = load_input_pipe(input_pipes[0])
    input_pipe_1 = load_input_pipe(input_pipes[1])

    train_feats = cont_feats + cat_feats
    print(train_feats)
    pred_names = []
    for m in masses:
        pred_name = f"dnn_mass{m}"
        pred_names.append(pred_name)
        events = ak.with_field(events, np.zeros(len(events), dtype=float), pred_name)
        np_preds = np.asarray(events[pred_name])

        for e, X, pipe, assign_mask in [
            (ensemble_0, X_1, input_pipe_0, (events.EventNumber % 2 == 1)),
            (ensemble_1, X_0, input_pipe_1, (events.EventNumber % 2 == 0)),
        ]:
            # predict
            mass_param = ParametrisedPrediction(
                train_feats,
                ['res_mass',]
                [preprocess_mass(m, cont_feats, pipe)],
            )
            preds = e.predict(X, cbs=[mass_param], verbose=False)
            # assign
            np_preds[assign_mask] = np.asarray(ak.flatten(preds))

    return ak.zip({pred_name: events[pred_name] for pred_name in pred_names})
