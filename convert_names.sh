#!/usr/bin/env bash
(return 0 2>/dev/null) && echo "This script must be run, not sourced. Try './' or 'bash'" && return 1

declare -A TABLE
DRYRUN="0"

### Argument parsing
HELP_STR="Prints this help message."
BASEPATH_STR="(String) Base directory path. Defaults to ${BASEPATH}."
DRYRUN_STR="(Boolean) Prints all the commands to be launched but does not launch them. Defaults to ${DRYRUN}."

function print_usage_submit_skims {
    USAGE="
        Run example: bash $(basename "$0") -d 

        -h / --help    [${HELP_STR}]
        -d             [${BASEPATH_STR}]
        -n / --dry-run [${DRYRUN_STR}]
"
    printf "${USAGE}"
}

while [[ $# -gt 0 ]]; do
    key=${1}
    case $key in
		-h|--help)
			print_usage_submit_skims
			exit 1
			;;
		-n|--dry-run)
			DRYRUN="1"
			shift;
			;;
		-d)
			BASEPATH=${2}
			shift; shift;
			;;
    esac
done

if [[ -z ${BASEPATH} ]]; then
    echo "Select the data folder via the '-d' option."
    exit 1;
fi

TABLE=(
    ["SKIM_VBF_BulkGraviton_m250"]="VBFToBulkGravitonToHHTo2B2Tau_M-250_"
    ["SKIM_VBF_BulkGraviton_m260"]="VBFToBulkGravitonToHHTo2B2Tau_M-260_"
    ["SKIM_VBF_BulkGraviton_m270"]="VBFToBulkGravitonToHHTo2B2Tau_M-270_"
    ["SKIM_VBF_BulkGraviton_m280"]="VBFToBulkGravitonToHHTo2B2Tau_M-280_"
    ["SKIM_VBF_BulkGraviton_m300"]="VBFToBulkGravitonToHHTo2B2Tau_M-300_"
    ["SKIM_VBF_BulkGraviton_m320"]="VBFToBulkGravitonToHHTo2B2Tau_M-320_"
    ["SKIM_VBF_BulkGraviton_m350"]="VBFToBulkGravitonToHHTo2B2Tau_M-350_"
    ["SKIM_VBF_BulkGraviton_m400"]="VBFToBulkGravitonToHHTo2B2Tau_M-400_"
    ["SKIM_VBF_BulkGraviton_m450"]="VBFToBulkGravitonToHHTo2B2Tau_M-450_"
    ["SKIM_VBF_BulkGraviton_m500"]="VBFToBulkGravitonToHHTo2B2Tau_M-500_"
    ["SKIM_VBF_BulkGraviton_m550"]="VBFToBulkGravitonToHHTo2B2Tau_M-550_"
    ["SKIM_VBF_BulkGraviton_m600"]="VBFToBulkGravitonToHHTo2B2Tau_M-600_"
    ["SKIM_VBF_BulkGraviton_m650"]="VBFToBulkGravitonToHHTo2B2Tau_M-650_"
    ["SKIM_VBF_BulkGraviton_m700"]="VBFToBulkGravitonToHHTo2B2Tau_M-700_"
    ["SKIM_VBF_BulkGraviton_m750"]="VBFToBulkGravitonToHHTo2B2Tau_M-750_"
    ["SKIM_VBF_BulkGraviton_m800"]="VBFToBulkGravitonToHHTo2B2Tau_M-800_"
    ["SKIM_VBF_BulkGraviton_m850"]="VBFToBulkGravitonToHHTo2B2Tau_M-850_"
    ["SKIM_VBF_BulkGraviton_m900"]="VBFToBulkGravitonToHHTo2B2Tau_M-900_"
    ["SKIM_VBF_BulkGraviton_m1000"]="VBFToBulkGravitonToHHTo2B2Tau_M-1000_"
    ["SKIM_VBF_BulkGraviton_m1250"]="VBFToBulkGravitonToHHTo2B2Tau_M-1250_"
    ["SKIM_VBF_BulkGraviton_m1500"]="VBFToBulkGravitonToHHTo2B2Tau_M-1500_"
    ["SKIM_VBF_BulkGraviton_m1750"]="VBFToBulkGravitonToHHTo2B2Tau_M-1750_"
    ["SKIM_VBF_BulkGraviton_m2000"]="VBFToBulkGravitonToHHTo2B2Tau_M-2000_"
    ["SKIM_VBF_BulkGraviton_m2500"]="VBFToBulkGravitonToHHTo2B2Tau_M-2500_"
    ["SKIM_VBF_BulkGraviton_m3000"]="VBFToBulkGravitonToHHTo2B2Tau_M-3000_"

    ["SKIM_VBF_Radion_m250"]="VBFToRadionToHHTo2B2Tau_M-250_"
    ["SKIM_VBF_Radion_m260"]="VBFToRadionToHHTo2B2Tau_M-260_"
    ["SKIM_VBF_Radion_m270"]="VBFToRadionToHHTo2B2Tau_M-270_"
    ["SKIM_VBF_Radion_m280"]="VBFToRadionToHHTo2B2Tau_M-280_"
    ["SKIM_VBF_Radion_m300"]="VBFToRadionToHHTo2B2Tau_M-300_"
    ["SKIM_VBF_Radion_m320"]="VBFToRadionToHHTo2B2Tau_M-320_"
    ["SKIM_VBF_Radion_m350"]="VBFToRadionToHHTo2B2Tau_M-350_"
    ["SKIM_VBF_Radion_m400"]="VBFToRadionToHHTo2B2Tau_M-400_"
    ["SKIM_VBF_Radion_m450"]="VBFToRadionToHHTo2B2Tau_M-450_"
    ["SKIM_VBF_Radion_m500"]="VBFToRadionToHHTo2B2Tau_M-500_"
    ["SKIM_VBF_Radion_m550"]="VBFToRadionToHHTo2B2Tau_M-550_"
    ["SKIM_VBF_Radion_m600"]="VBFToRadionToHHTo2B2Tau_M-600_"
    ["SKIM_VBF_Radion_m650"]="VBFToRadionToHHTo2B2Tau_M-650_"
    ["SKIM_VBF_Radion_m700"]="VBFToRadionToHHTo2B2Tau_M-700_"
    ["SKIM_VBF_Radion_m750"]="VBFToRadionToHHTo2B2Tau_M-750_"
    ["SKIM_VBF_Radion_m800"]="VBFToRadionToHHTo2B2Tau_M-800_"
    ["SKIM_VBF_Radion_m850"]="VBFToRadionToHHTo2B2Tau_M-850_"
    ["SKIM_VBF_Radion_m900"]="VBFToRadionToHHTo2B2Tau_M-900_"
    ["SKIM_VBF_Radion_m1000"]="VBFToRadionToHHTo2B2Tau_M-1000_"
    ["SKIM_VBF_Radion_m1250"]="VBFToRadionToHHTo2B2Tau_M-1250_"
    ["SKIM_VBF_Radion_m1500"]="VBFToRadionToHHTo2B2Tau_M-1500_"
    ["SKIM_VBF_Radion_m1750"]="VBFToRadionToHHTo2B2Tau_M-1750_"
    ["SKIM_VBF_Radion_m2000"]="VBFToRadionToHHTo2B2Tau_M-2000_"
    ["SKIM_VBF_Radion_m2500"]="VBFToRadionToHHTo2B2Tau_M-2500_"
    ["SKIM_VBF_Radion_m3000"]="VBFToRadionToHHTo2B2Tau_M-3000_"

    ["SKIM_ggF_Radion_m250"]="GluGluToRadionToHHTo2B2Tau_M-250_"
    ["SKIM_ggF_Radion_m260"]="GluGluToRadionToHHTo2B2Tau_M-260_"
    ["SKIM_ggF_Radion_m270"]="GluGluToRadionToHHTo2B2Tau_M-270_"
    ["SKIM_ggF_Radion_m280"]="GluGluToRadionToHHTo2B2Tau_M-280_"
    ["SKIM_ggF_Radion_m300"]="GluGluToRadionToHHTo2B2Tau_M-300_"
    ["SKIM_ggF_Radion_m320"]="GluGluToRadionToHHTo2B2Tau_M-320_"
    ["SKIM_ggF_Radion_m350"]="GluGluToRadionToHHTo2B2Tau_M-350_"
    ["SKIM_ggF_Radion_m400"]="GluGluToRadionToHHTo2B2Tau_M-400_"
    ["SKIM_ggF_Radion_m450"]="GluGluToRadionToHHTo2B2Tau_M-450_"
    ["SKIM_ggF_Radion_m500"]="GluGluToRadionToHHTo2B2Tau_M-500_"
    ["SKIM_ggF_Radion_m550"]="GluGluToRadionToHHTo2B2Tau_M-550_"
    ["SKIM_ggF_Radion_m600"]="GluGluToRadionToHHTo2B2Tau_M-600_"
    ["SKIM_ggF_Radion_m650"]="GluGluToRadionToHHTo2B2Tau_M-650_"
    ["SKIM_ggF_Radion_m700"]="GluGluToRadionToHHTo2B2Tau_M-700_"
    ["SKIM_ggF_Radion_m750"]="GluGluToRadionToHHTo2B2Tau_M-750_"
    ["SKIM_ggF_Radion_m800"]="GluGluToRadionToHHTo2B2Tau_M-800_"
    ["SKIM_ggF_Radion_m850"]="GluGluToRadionToHHTo2B2Tau_M-850_"
    ["SKIM_ggF_Radion_m900"]="GluGluToRadionToHHTo2B2Tau_M-900_"
    ["SKIM_ggF_Radion_m1000"]="GluGluToRadionToHHTo2B2Tau_M-1000_"
    ["SKIM_ggF_Radion_m1250"]="GluGluToRadionToHHTo2B2Tau_M-1250_"
    ["SKIM_ggF_Radion_m1500"]="GluGluToRadionToHHTo2B2Tau_M-1500_"
    ["SKIM_ggF_Radion_m1750"]="GluGluToRadionToHHTo2B2Tau_M-1750_"
    ["SKIM_ggF_Radion_m2000"]="GluGluToRadionToHHTo2B2Tau_M-2000_"
    ["SKIM_ggF_Radion_m2500"]="GluGluToRadionToHHTo2B2Tau_M-2500_"
    ["SKIM_ggF_Radion_m3000"]="GluGluToRadionToHHTo2B2Tau_M-3000_"

    ["SKIM_ggF_BulkGraviton_m250"]="GluGluToBulkGravitonToHHTo2B2Tau_M-250_"
    ["SKIM_ggF_BulkGraviton_m260"]="GluGluToBulkGravitonToHHTo2B2Tau_M-260_"
    ["SKIM_ggF_BulkGraviton_m270"]="GluGluToBulkGravitonToHHTo2B2Tau_M-270_"
    ["SKIM_ggF_BulkGraviton_m280"]="GluGluToBulkGravitonToHHTo2B2Tau_M-280_"
    ["SKIM_ggF_BulkGraviton_m300"]="GluGluToBulkGravitonToHHTo2B2Tau_M-300_"
    ["SKIM_ggF_BulkGraviton_m320"]="GluGluToBulkGravitonToHHTo2B2Tau_M-320_"
    ["SKIM_ggF_BulkGraviton_m350"]="GluGluToBulkGravitonToHHTo2B2Tau_M-350_"
    ["SKIM_ggF_BulkGraviton_m400"]="GluGluToBulkGravitonToHHTo2B2Tau_M-400_"
    ["SKIM_ggF_BulkGraviton_m450"]="GluGluToBulkGravitonToHHTo2B2Tau_M-450_"
    ["SKIM_ggF_BulkGraviton_m500"]="GluGluToBulkGravitonToHHTo2B2Tau_M-500_"
    ["SKIM_ggF_BulkGraviton_m550"]="GluGluToBulkGravitonToHHTo2B2Tau_M-550_"
    ["SKIM_ggF_BulkGraviton_m600"]="GluGluToBulkGravitonToHHTo2B2Tau_M-600_"
    ["SKIM_ggF_BulkGraviton_m650"]="GluGluToBulkGravitonToHHTo2B2Tau_M-650_"
    ["SKIM_ggF_BulkGraviton_m700"]="GluGluToBulkGravitonToHHTo2B2Tau_M-700_"
    ["SKIM_ggF_BulkGraviton_m750"]="GluGluToBulkGravitonToHHTo2B2Tau_M-750_"
    ["SKIM_ggF_BulkGraviton_m800"]="GluGluToBulkGravitonToHHTo2B2Tau_M-800_"
    ["SKIM_ggF_BulkGraviton_m850"]="GluGluToBulkGravitonToHHTo2B2Tau_M-850_"
    ["SKIM_ggF_BulkGraviton_m900"]="GluGluToBulkGravitonToHHTo2B2Tau_M-900_"
    ["SKIM_ggF_BulkGraviton_m1000"]="GluGluToBulkGravitonToHHTo2B2Tau_M-1000_"
    ["SKIM_ggF_BulkGraviton_m1250"]="GluGluToBulkGravitonToHHTo2B2Tau_M-1250_"
    ["SKIM_ggF_BulkGraviton_m1500"]="GluGluToBulkGravitonToHHTo2B2Tau_M-1500_"
    ["SKIM_ggF_BulkGraviton_m1750"]="GluGluToBulkGravitonToHHTo2B2Tau_M-1750_"
    ["SKIM_ggF_BulkGraviton_m2000"]="GluGluToBulkGravitonToHHTo2B2Tau_M-2000_"
    ["SKIM_ggF_BulkGraviton_m2500"]="GluGluToBulkGravitonToHHTo2B2Tau_M-2500_"
    ["SKIM_ggF_BulkGraviton_m3000"]="GluGluToBulkGravitonToHHTo2B2Tau_M-3000_"

    ["SKIM_WZZ"]="54_WZZ"
    ["SKIM_ZZZ"]="56_ZZZ"
    ["SKIM_WWZ"]="52_WWZ"
    ["SKIM_WWW"]="50_WWW"

    ["SKIM_ZZ"]="_ZZ_TuneCP5"
    ["SKIM_WW"]="_WW_TuneCP5"
    ["SKIM_WZ"]="_WZ_TuneCP5"

    ["SKIM_TTWJetsToQQ"]="TTWJetsToQQ"
    ["SKIM_TTWJetsToLNu"]="TTWJetsToLNu"
    ["SKIM_TTWZ"]="TTWZ"
    ["SKIM_TTZZ"]="TTZZ"
    ["SKIM_TTWW"]="TTWW"
    ["SKIM_TTZToLLNuNu"]="TTZToLLNuNu"

    ["SKIM_ttHTobb"]="ttHTobb"
    ["SKIM_ttHToNonbb"]="ttHToNonbb"
    ["SKIM_ttHToTauTau"]="ttHToTauTau"

    ["SKIM_DY_amc_incl"]="DYJetsToLL_M-50_TuneCP5_13TeV-amc"
    ["SKIM_DY_amc_0j"]="DYJetsToLL_0J"
    ["SKIM_DY_amc_1j"]="DYJetsToLL_1J"
    ["SKIM_DY_amc_2j"]="DYJetsToLL_2J"
    ["SKIM_DY_amc_PtZ_0To50"]="DYJetsToLL_LHEFilterPtZ-0To50"
    ["SKIM_DY_amc_PtZ_50To100"]="DYJetsToLL_LHEFilterPtZ-50To100"
    ["SKIM_DY_amc_PtZ_100To250"]="DYJetsToLL_LHEFilterPtZ-100To250"
    ["SKIM_DY_amc_PtZ_250To400"]="DYJetsToLL_LHEFilterPtZ-250To400"
    ["SKIM_DY_amc_PtZ_400To650"]="DYJetsToLL_LHEFilterPtZ-400To650"
    ["SKIM_DY_amc_PtZ_650ToInf"]="DYJetsToLL_LHEFilterPtZ-650ToInf"

    ["SKIM_ST_tchannel_antitop"]="ST_t-channel_antitop"
    ["SKIM_ST_tchannel_top"]="ST_t-channel_top"
    ["SKIM_ST_tW_top"]="ST_tW_top_5f_inclusive"
    ["SKIM_ST_tW_antitop"]="ST_tW_antitop_5f_inclusive"

    ["SKIM_EWKWMinus2Jets_WToLNu"]="EWKWMinus2Jets_WToLNu"
    ["SKIM_EWKWPlus2Jets_WToLNu"]="EWKWPlus2Jets_WToLNu"
    ["SKIM_EWKZ2Jets_ZToLL"]="EWKZ2Jets_ZToLL"

    ["SKIM_VBFHToTauTau"]="VBFHToTauTau"
    ["SKIM_ZHToTauTau"]="ZHToTauTau"

    ["SKIM_WminusHToTauTau"]="WminusHToTauTau"
    ["SKIM_WplusHToTauTau"]="WplusHToTauTau"

    ["SKIM_GluGluHToTauTau"]="GluGluHToTauTau"

    ["SKIM_WJets_HT0To70"]="WJetsToLNu_TuneCP5_13TeV-madgraph"
    ["SKIM_WJets_HT70To100"]="WJetsToLNu_HT-70To100"
    ["SKIM_WJets_HT100To200"]="WJetsToLNu_HT-100To200"
    ["SKIM_WJets_HT200To400"]="WJetsToLNu_HT-200To400"
    ["SKIM_WJets_HT400To600"]="WJetsToLNu_HT-400To600"
    ["SKIM_WJets_HT600To800"]="WJetsToLNu_HT-600To800"
    ["SKIM_WJets_HT800To1200"]="WJetsToLNu_HT-800To1200"
    ["SKIM_WJets_HT1200To2500"]="WJetsToLNu_HT-1200To2500"
    ["SKIM_WJets_HT2500ToInf"]="WJetsToLNu_HT-2500ToInf"

    ["SKIM_TT_fullyHad"]="TTToHadronic"
    ["SKIM_TT_semiLep"]="TTToSemiLeptonic"
    ["SKIM_TT_fullyLep"]="TTTo2L2Nu"

    #["SKIM_GGHH_SM"]=""
)

for key in ${!TABLE[@]}; do
    value=${TABLE[${key}]}

    if [ -d ${BASEPATH}/${value} ]; then
		comm="mv ${BASEPATH}/${value} ${BASEPATH}/${key}"
		[[ ${DRYRUN} -eq 1 ]] && echo ${comm} || ${comm}
    fi
done
