klub_index_cols = ["EventNumber", "RunNumber", "lumi"]

klub_H_cols = [ "tauH_mass", "tauH_pt", "tauH_eta", "tauH_phi", "tauH_e",
    "tauH_SVFIT_pt", "tauH_SVFIT_eta", "tauH_SVFIT_phi", "tauH_SVFIT_mass",
    "bH_mass", "bH_pt", "bH_eta", "bH_phi", "bH_e",
    "HH_mass", "HH_mass_raw", "HH_pt", "HH_eta", "HH_phi", "HH_e",
    "HHKin_mass_raw", "HHKin_mass_raw_chi2", "MT2",
]

klub_selection_cols = [
    "pairType",
    "nleps",
    "nbjetscand",
    "isLeptrigger",
    "bjet1_bID_deepFlavor",
    "bjet2_bID_deepFlavor",
    "isBoosted",
]

klub_lep_cols = [
    "dau1_pt", "dau1_eta", "dau1_phi", "dau1_e", "dau1_iso", "dau1_eleMVAiso",
    "dau2_pt", "dau2_eta", "dau2_phi", "dau2_e",
]

klub_met_cols = [
    "met_et",
    "met_phi",
    "met_cov00",
    "met_cov01",
    "met_cov11",
]
klub_b_cols = [
    "bjet1_pt", "bjet1_eta", "bjet1_phi", "bjet1_e", "bjet1_HHbtag", "bjet1_CvsL", "bjet1_CvsB",
    "bjet2_pt", "bjet2_eta", "bjet2_phi", "bjet2_e", "bjet2_HHbtag", "bjet2_CvsL", "bjet2_CvsB",
]

klub_vbf_cols = [
    "VBFjj_mass", "VBFjj_deltaEta",
    "VBFjet1_pt", "VBFjet1_eta", "VBFjet1_phi", "VBFjet1_e", "VBFjet1_HHbtag", "VBFjet1_CvsL", "VBFjet1_CvsB",
    "VBFjet2_pt", "VBFjet2_eta", "VBFjet2_phi", "VBFjet2_e", "VBFjet2_HHbtag", "VBFjet2_CvsL", "VBFjet2_CvsB",
]
klub_region_cols = [
    "isVBFtrigger",
    "isVBF",
    "isOS",
    "dau1_deepTauVsJet",
    "dau2_deepTauVsJet",
]

nn_columns = klub_index_cols + klub_H_cols + klub_selection_cols + klub_lep_cols + klub_met_cols + klub_b_cols + klub_vbf_cols + klub_region_cols
