#include <iostream>
#include <string>
#include<TFile.h>
#include "TTree.h"
#include "TBranch.h"


void show_help() {
    /* Show help for input arguments */
    std::cout << "-i : input root file (containing predictions), no default \n";
    std::cout << "-t : target root file, no default \n";
    std::cout << "-n : branch name, default: nonparam_baseline \n";
    std::cout << "-p : parametrised, default: false \n";
}


std::map<std::string, std::string> get_options(int argc, char* argv[]) {
    /*Interpret input arguments*/

    std::map<std::string, std::string> options;
    options.insert(std::make_pair("-i", std::string())); // model root name
    options.insert(std::make_pair("-t", std::string()));
    options.insert(std::make_pair("-n", std::string("nonparam_baseline")));
    options.insert(std::make_pair("-p", std::string("false")));

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


bool fill_new_branch(std::string targ_file, std::string predictions_file) {
    //if (!boost::filesystem::exists(targ_file)) {
        //throw std::invalid_argument("File: " + targ_file + " not found");
        //return false;
    //}

    Int_t Run,  Lumi, fRun, fLumi;
    ULong64_t Event, fEvent;
    Double_t dnn_output; 

    std::cout << "Opening " << targ_file << "\n";
    TFile *f = new TFile(targ_file.c_str(), "update");
    TTree *klub_tree  = (TTree*)f->Get("HTauTauTree");
    TBranch *newbranch = klub_tree->Branch("DNN", &dnn_output, "DNN/F");

    std::cout << "Opening " << predictions_file << "\n";
    TFile *pred_file = new TFile(predictions_file.c_str());
    TTree *pred_tree = (TTree*)pred_file->Get("evaluation");

    klub_tree->SetBranchAddress("RunNumber",&Run);
    klub_tree->SetBranchAddress("EventNumber",&Event);
    klub_tree->SetBranchAddress("lumi",&Lumi);
    pred_tree->SetBranchAddress("RunNumber",&fRun);
    pred_tree->SetBranchAddress("EventNumber",&fEvent);
    pred_tree->SetBranchAddress("lumi",&fLumi);
    pred_tree->SetBranchAddress("dnn_output", &dnn_output);
    klub_tree->AddFriend(pred_tree);
    
    Long64_t nentries = klub_tree->GetEntries();
    for (Long64_t i=0;i<nentries;i++) {
        klub_tree->GetEntry(i);
        if (fRun == Run && fEvent==Event && fLumi==Lumi) {
            pred_tree->GetEntryWithIndex(Run,Event);
            newbranch->Fill();
        }
        else{
            printf("Files don't seem to match");
        }
    }
    delete f;
    delete pred_file; 
    return true;
}


bool fill_new(std::string targ_file, std::string predictions_file, std::string branch_name) {
    //if (!boost::filesystem::exists(targ_file)) {
        //throw std::invalid_argument("File: " + targ_file + " not found");
        //return false;
    //}

    Double_t dnn_output; 

    std::cout << "Opening " << predictions_file << "\n";
    TFile *pred_file = new TFile(predictions_file.c_str());
    TTree *pred_tree = (TTree*)pred_file->Get("evaluation");
    pred_tree->SetBranchAddress(std::string("dnn_"+branch_name).c_str(), &dnn_output);

    std::cout << "Opening " << targ_file << "\n";
    TFile *f = new TFile(targ_file.c_str(), "update");
    TTree *klub_tree  = (TTree*)f->Get("HTauTauTree");
    TBranch *newbranch = klub_tree->Branch(std::string("dnn_"+branch_name).c_str(), &dnn_output, std::string("dnn_"+branch_name+"/D").c_str());

    
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
    std::cout << "Running add_branch \n";
    bool parametrised = options["-p"] == "true";
    if (parametrised){
        int masses[25] = {250, 260, 270, 280, 300, 320, 350, 400,
                          450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 1000,
                          1250, 1500, 1750, 2000, 2500, 3000};
        int spins[2] = {0, 2};
        // loop over spins
        for (int i = 0; i < 2; i++)
        {
            // loop over masses
            for (int j = 0; j < 25; j++)
            {
                int mass = masses[j];
                int spin = spins[i];
                std::string branch_name(options["-n"]);
                branch_name += "_spin"+std::to_string(spin)+"_mass"+std::to_string(mass);
                fill_new(options["-t"], options["-i"], branch_name);
            }
        }
    }
    else{
        fill_new(options["-t"], options["-i"], options["-n"]);
    }
}