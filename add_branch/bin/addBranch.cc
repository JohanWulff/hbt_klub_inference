#include <iostream>
#include <string>
#include<TFile.h>
#include "TTree.h"
#include "TBranch.h"


void show_help() {
    /* Show help for input arguments */
    std::cout << "-i : input root file (containing predictions), no default \n";
    std::cout << "-t : target root file, no default \n";
    std::cout << "-n : model name, no default\n";
    std::cout << "-m : multiclass, default: false \n";
    //std::cout << "-p : parametrised, default: false \n";
}


std::map<std::string, std::string> get_options(int argc, char* argv[]) {
    /*Interpret input arguments*/

    std::map<std::string, std::string> options;
    options.insert(std::make_pair("-i", std::string()));
    options.insert(std::make_pair("-t", std::string()));
    options.insert(std::make_pair("-n", std::string("hbtresdnn")));
    options.insert(std::make_pair("-m", std::string("false")));
    //options.insert(std::make_pair("-p", std::string("false")));
    if (argc >= 2) { //Check if help was requested
        std::string option(argv[1]);
        if (option == "-h" || option == "--help") {
            show_help();
            options.clear();
            return options;
        }
    }

    for (int i = 1; i < argc; i = i+2) {
        std::string option(argv[i]);
        std::string argument(argv[i+1]);
        if (option == "-h" || option == "--help" || argument == "-h" || argument == "--help") { // Check if help was requested
            show_help();
            options.clear();
            return options;
        }
        options[option] = argument;
    }
    return options;
}


bool fill_new(std::string targ_file, std::string predictions_file, std::string model_name) {

    Float_t dnn_output; 

    TFile *pred_file = new TFile(predictions_file.c_str());
    TTree *pred_tree = (TTree*)pred_file->Get("evaluation");
    pred_tree->SetBranchAddress(std::string(model_name).c_str(), &dnn_output);

    TFile *f = new TFile(targ_file.c_str(), "update");
    TTree *klub_tree  = (TTree*)f->Get("HTauTauTree");
    TBranch *newbranch = klub_tree->Branch(std::string(model_name).c_str(), &dnn_output, std::string(model_name+"/F").c_str());

    
    Long64_t nentries = klub_tree->GetEntries();
    Long64_t nentries_p = pred_tree->GetEntries();
    if (nentries != nentries_p){
        std::cout << "Number of Entries in both trees don't match" << std::endl;
        return false;
    }
    for (Long64_t i=0;i<nentries;i++) {
        pred_tree->GetEntry(i);
        newbranch->Fill();
    }
    klub_tree->Write();
    delete pred_file;
    delete f;
    return true;
}


int main(int argc, char *argv[]){
    std::map<std::string, std::string> options = get_options(argc, argv); // Parse arguments
    if (options.size() == 0) {
        return 1;
    }
    // branch naming convention: hbtresdnn_mass[250-3000]_spin[0,2]_[hh,dy,tt]
    std::cout << "Running add_branch with options:\n";
    //bool parametrised = options["-p"] == "true";
    bool multiclass = options["-m"] == "true";
    std::cout << "input file (-i): " << options["-i"] << "\n";
    std::cout << "target file (-t): " << options["-t"] << "\n";
    std::cout << "name (-n): " << options["-n"] << "\n";
    //std::cout << "parametrised (-p): " << options["-p"] << "\n";
    std::cout << "multiclass (-m): " << options["-m"] << "\n";

    
    int masses[25] = {250, 260, 270, 280, 300, 320, 350, 400,
                        450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 1000,
                        1250, 1500, 1750, 2000, 2500, 3000};
    int spins[2] = {0, 2};
    std::string classes[3] = {"hh", "tt", "dy"};
    // loop over spins
    for (int i = 0; i < 2; i++)
    {
        // loop over masses
        for (int j = 0; j < 25; j++)
        {
            int mass = masses[j];
            int spin = spins[i];
            // loop over classes
            if (multiclass){
                for (int k = 0; k < 3; k++){
                    std::string branch_name(options["-n"]);
                    std::string class_name = classes[k];
                    branch_name += "_mass"+std::to_string(mass)+"_spin"+std::to_string(spin)+"_"+class_name;
                    fill_new(options["-t"], options["-i"], branch_name);
                }
            }
            else{
                std::string branch_name(options["-n"]);
                branch_name += "_mass"+std::to_string(mass)+"_spin"+std::to_string(spin);
                fill_new(options["-t"], options["-i"], branch_name);
            }
        }
    }
}