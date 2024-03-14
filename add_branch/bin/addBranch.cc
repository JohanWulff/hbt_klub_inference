#include <iostream>
#include <string>
#include <fstream>

#include <TFile.h>
#include <TTree.h>
#include <TBranch.h>


void show_help() {
    /* Show help for input arguments */
    std::cout << "-i : input root file (containing predictions), no default \n";
    std::cout << "-t : target root file, no default \n";
    std::cout << "-n : model name, no default"; 
}


std::map<std::string, std::string> get_options(int argc, char* argv[]) {
    /*Interpret input arguments*/

    std::map<std::string, std::string> options;
    options.insert(std::make_pair("-i", std::string()));
    options.insert(std::make_pair("-t", std::string()));
    options.insert(std::make_pair("--branches", std::string()));
    options.insert(std::make_pair("--input_tree", std::string("hbtres")));
    options.insert(std::make_pair("--target_tree", std::string("HTauTauTree")));
    options.insert(std::make_pair("-n", std::string("hbtresdnn")));
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


bool fill_new(std::string targ_file,
              std::string predictions_file,
              std::string branch_name,
              std::string targ_treename = "HTauTauTree",
              std::string pred_treename = "hbtres") {

    Float_t dnn_output; 

    TFile *pred_file = new TFile(predictions_file.c_str());
    TTree *pred_tree = (TTree*)pred_file->Get(pred_treename.c_str());
    pred_tree->SetBranchAddress(std::string(branch_name).c_str(), &dnn_output);

    TFile *f = new TFile(targ_file.c_str(), "update");
    TTree *klub_tree  = (TTree*)f->Get(targ_treename.c_str());
    TBranch *newbranch = klub_tree->Branch(std::string(branch_name).c_str(), &dnn_output, std::string(branch_name+"/F").c_str());

    
    Long64_t nentries = klub_tree->GetEntries();
    //Long64_t nentries_p = pred_tree->GetEntries();
    //if (nentries != nentries_p){
        //std::cout << "Number of Entries in both trees don't match" << std::endl;
        //return false;
    //}
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
    std::cout << "input file (-i): " << options["-i"] << "\n";
    std::cout << "target file (-t): " << options["-t"] << "\n";
    std::cout << "branches file (--branches): " << options["--branches"] << "\n";
    std::cout << "input tree name (--input_tree): " << options["--input_tree"] << "\n";
    std::cout << "target tree name (--target_tree): " << options["--target_tree"] << "\n";
    std::cout << "model name (-n): " << options["-n"] << "\n";


    // instead of hardcoding all of the branches, we read them from a file
    std::string branch;
    std::ifstream branches_file;
    branches_file.open(options["--branches"]);
    
    while (std::getline(branches_file, branch)) {
        fill_new(options["-t"], options["-i"], branch, options["--target_tree"], options["--input_tree"]);
    }
    branches_file.close();
}