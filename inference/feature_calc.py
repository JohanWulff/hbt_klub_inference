from typing import List
import numpy as np
import awkward as ak
import vector
import pickle

from helpers import get_num_btag, get_vbf_pair, jet_cat_lookup, adjust_svfit_feats
from helpers import calc_mt, calc_top_masses, get_jet_quality

id2year = {0: 2016, 1: 2017, 2: 2018}
year2id = {id2year[i]: i for i in id2year}

id2spin = {0:'radion', 1:'graviton', 2:'scalar'}
spin2id = {id2spin[i]:i for i in id2spin}
spin2val = {'radion': 0, 'graviton': 2, 'scalar': 0}
id2val = {
    i: spin2val[name]
    for i, name in id2spin.items()
}


def fix_sv_feats(events, feats, fix_val = -1):
    sv_fit_conv = events.tauH_SVFIT_mass>0
    for feat in feats:
        np_feat = events[feat].to_numpy()
        np_feat[~sv_fit_conv] = fix_val*np.ones(ak.sum(~sv_fit_conv))
    return events


def load_input_pipe(name:str):
    with open(name, 'rb') as fin: input_pipe = pickle.load(fin)
    return input_pipe


def struct_to_float_array(arr):
    return arr.astype([(name, np.float32) for name in arr.dtype.names], copy=False).view(np.float32).reshape((-1, len(arr.dtype)))


#def preprocess_mass(m, feats_param, pipe):
#    idx = set_0_fy.cont_feats.index('res_mass')
#    m -= pipe[0].mean_[idx]
#    m /= pipe[0].scale_[idx]
#    return m

def calc_feats(events: ak.Array, mass: int, spin: int, year: int) -> ak.Array:
    events = get_vbf_pair(events=events)
    events = get_num_btag(events=events)
    events = jet_cat_lookup(events=events)
    sv_fit = vector.array({"pt": events.tauH_SVFIT_pt, "eta": events.tauH_SVFIT_eta,
                            "phi": events.tauH_SVFIT_phi, "mass": events.tauH_SVFIT_mass,}).to_rhophietatau()
    l_1 = vector.array({"pt": events.dau1_pt, "eta": events.dau1_eta,
                        "phi": events.dau1_phi, "mass": events.dau1_e,}).to_rhophietatau()
    l_2 = vector.array({"pt": events.dau2_pt, "eta": events.dau2_eta,
                        "phi": events.dau2_phi, "mass": events.dau2_e,}).to_rhophietatau()
    b_1 = vector.array({"pt": events.bjet1_pt, "eta": events.bjet1_eta,
                        "phi": events.bjet1_phi, "mass": events.bjet1_e,}).to_rhophietatau()
    b_2 = vector.array({"pt": events.bjet2_pt, "eta": events.bjet2_eta,
                            "phi": events.bjet2_phi, "mass": events.bjet2_e,}).to_rhophietatau()
    met = vector.array({"pt": events.met_et, "eta": np.zeros(len(events)),
            "phi": events.met_phi, "mass": np.zeros(len(events)), })
    # continuous feats
    events['res_mass'] = mass*np.ones(len(events))
    # calculate vector-related feats
    events['dR_l1_l2'] = l_1.deltaR(l_2)
    events['dR_b1_b2'] = b_1.deltaR(b_2)
    events['deta_l1_l2'] = l_1.deltaeta(l_2)
    events['dR_l1_l2_x_sv_pT'] = events.dR_l1_l2*sv_fit.pt
    events['sv_mass'] = sv_fit.mass
    events['sv_E'] = sv_fit.energy
    events['met_pT'] = met.pt
    events['ll_mt'] = (l_1+l_2).mt
    # let's not store these 4vectors in events
    h_bb = b_1+b_2
    h_tt_vis = l_1+l_2
    h_tt_met = h_tt_vis+met

    hh = vector.array({"px": h_bb.px+sv_fit.px, "py": h_bb.py+sv_fit.py,
                    "pz": h_bb.pz+sv_fit.pz, "mass": events.HHKin_mass_raw,}).to_rhophietatau()

    h_bb_tt_met_kinfit = vector.array({"px": h_bb.px+h_tt_met.px, "py": h_bb.py+h_tt_met.py,
                                "pz": h_bb.pz+h_tt_met.pz, "mass": events.HHKin_mass_raw}).to_rhophietatau()
    hh_kinfit_chi2 = events.HHKin_mass_raw_chi2.to_numpy()
    inf_mask = (hh_kinfit_chi2 == np.inf) | (hh_kinfit_chi2 == -np.inf)
    hh_kinfit_chi2[inf_mask] = -1*np.ones(ak.sum(inf_mask)) 
    hh_kinfit_conv = hh_kinfit_chi2>0
    hh_kinfit_chi2[~hh_kinfit_conv] = -1*np.ones(ak.sum(~hh_kinfit_conv)) 
    sv_fit_conv = events.tauH_SVFIT_mass>0
    hh[np.logical_and(~hh_kinfit_conv, sv_fit_conv)] = (h_bb+sv_fit)[np.logical_and(~hh_kinfit_conv, sv_fit_conv)]
    hh[np.logical_and(~hh_kinfit_conv, ~sv_fit_conv)] = (h_bb+h_tt_met)[np.logical_and(~hh_kinfit_conv, ~sv_fit_conv)]
    hh[np.logical_and(hh_kinfit_conv, ~sv_fit_conv)] = h_bb_tt_met_kinfit[np.logical_and(hh_kinfit_conv, ~sv_fit_conv)]

    events = fix_sv_feats(events, feats=['sv_mass', 'sv_E', 'dR_l1_l2_x_sv_pT'])
    events['hh_pT'] = hh.pt
    events['h_bb_mass'] = h_bb.m
    events['diH_mass_met'] = (h_bb+h_tt_met).M
    events['deta_hbb_httvis'] = h_bb.deltaeta(h_tt_vis)
    events['dphi_hbb_met'] = h_bb.deltaphi(met)

    # set sv_mt to -1 as default
    events['sv_mt'] = -1*np.ones(len(events))
    # calculate sv_mt only for events where sv_fit converged (mass > 0)
    np_sv_mt = np.asarray(ak.flatten(events.sv_mt, axis=0))
    np_sv_mass = np.asarray(ak.flatten(events.sv_mass, axis=0))
    np_sv_mt[np_sv_mass > 0] = calc_mt(v=sv_fit[np_sv_mass > 0], met=met[np_sv_mass > 0])

    events['l_1_mt'] = calc_mt(v=l_1, met=met)
    events['l_2_mt'] = calc_mt(v=l_2, met=met)

    top_masses = calc_top_masses(l_1=l_1, l_2=l_2, b_1=b_1, b_2=b_2, met=met)
    events['top_1_mass'] = np.array([i[0] for i in top_masses], dtype='float32')
    events['top_2_mass'] = np.array([i[1] for i in top_masses], dtype='float32')
    # other features are already calculated:
    # - KLUB Name ------------------ Giles' Name --------
    # events.dau1_pt                "l_1_pt"
    # events.dau2_pt                "l_2_pt"
    # events.HHKin_mass_raw_chi2    "hh_kinfit_chi2"; was assigned nans in giles' processing if < 0
    # events.bjet1_CvsL             "b1_cvsl_raw"
    # events.bjet2_CvsL             "b2_cvsl_raw"
    # events.HHKin_mass_raw         "hh_kinfit_mass"; was assigned nans if kinfit_chi2 < 0
    # events.bjet1_HHbtag           "b1_hhbtag"
    # events.bjet2_HHbtag           "b2_hhbtag"
    # events.has_vbf_pair           "is_vbf"

    # categorical feats
    # events.isBoosted              "boosted"
    #
    #
    #   super confusing..
    #
    #    channel | Giles' channel ID | pairType
    #   --------------------------------------
    #    mutau   |    1              |   0
    #    etau    |    2              |   1
    #    tautau  |    0              |   2

    np_channel = np.asarray(ak.flatten(events.pairType, axis=0))
    np_channel += 1 
    # set channel to 0 everywhere, where its 3 which is tautau
    np_channel[np_channel==3] = np.zeros(len(np_channel[np_channel==3]))
    events['channel'] = np_channel
    events['spin'] = spin*np.ones(len(events))
    events['year'] = year2id[2018]*np.ones(len(events))
    # calculate jet quality. TODO: Check if the WP's are still correct
    get_jet_quality(events=events, year=year)
    # calculate cvsb wp flags
    #for jet_idx in [1, 2]:
    #    for score in [f'bjet{jet_idx}_CvsB', f'bjet{jet_idx}_CvsL']:
    #        if score.endswith('B'):
    #            events[f'b_{jet_idx}_cvsb'] = get_cvsb_flag(score=events[score])
    #        if score.endswith('L'):
    #            # note to marcel and tobias: I know tat this applies the cvsb wp to the cvsl score
    #            # which is probably wrong. But it was done like this so far so i should keep it for now
    #            events[f'b_{jet_idx}_cvsl'] = get_cvsb_flag(score=events[score])

    events = adjust_svfit_feats(events=events)
    return events


def prepare_feats(events: ak.Array, cont_feats: List, cat_feats: List, input_pipes: List[str]):
    input_pipe_0 = load_input_pipe(input_pipes[0])
    input_pipe_1 = load_input_pipe(input_pipes[1])

    cont_feats_0 = events[cont_feats, events.EventNumber%2 == 0].to_numpy()
    cat_feats_0 = events[cat_feats, events.EventNumber%2 == 0].to_numpy()
    cont_feats_1 = events[cont_feats, events.EventNumber%2 == 1].to_numpy()
    cat_feats_1 = events[cat_feats, events.EventNumber%2 == 1].to_numpy()

    cont_feats_0 = struct_to_float_array(cont_feats_0)
    cat_feats_0 = struct_to_float_array(cat_feats_0)
    cont_feats_1 = struct_to_float_array(cont_feats_1)
    cat_feats_1 = struct_to_float_array(cat_feats_1)

    cont_feats_0 = input_pipe_0.transform(cont_feats_0)
    cont_feats_1 = input_pipe_1.transform(cont_feats_1)

    X_0 = np.hstack([cont_feats_0, cat_feats_0])
    X_1 = np.hstack([cont_feats_1, cat_feats_1])
    return X_0, X_1

