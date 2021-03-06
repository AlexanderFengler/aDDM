#!/usr/bin/python

# run_model.py
# Author: Gabriela Tavares, gtavares@caltech.edu


import numpy as np
import sys

from handle_fixations import load_data_from_csv, analysis_per_trial


def run_analysis(rt, choice, valueLeft, valueRight, fixItem, fixTime, d, theta,
    std, useOddTrials=True, useEvenTrials=True):
    trialsPerSubject = 1200
    logLikelihood = 0
    subjects = rt.keys()
    for subject in subjects:
        print("Running subject " + subject + "...")
        trials = rt[subject].keys()
        trialSet = np.random.choice(trials, trialsPerSubject, replace=False)
        for trial in trialSet:
            if not useOddTrials and trial % 2 != 0:
                continue
            if not useEvenTrials and trial % 2 == 0:
                continue
            likelihood = analysis_per_trial(rt[subject][trial],
                choice[subject][trial], valueLeft[subject][trial],
                valueRight[subject][trial], fixItem[subject][trial],
                fixTime[subject][trial], d, theta, std=std)
            if likelihood != 0:
                logLikelihood += np.log(likelihood)
    return -logLikelihood


def main(argv):
    d = float(argv[0])
    std = float(argv[1])
    theta = float(argv[2])

    # Load experimental data from CSV file.
    data = load_data_from_csv("expdata.csv", "fixations.csv")
    rt = data.rt
    choice = data.choice
    distLeft = data.distLeft
    distRight = data.distRight
    fixItem = data.fixItem
    fixTime = data.fixTime

    # Get item values.
    valueLeft = dict()
    valueRight = dict()
    subjects = distLeft.keys()
    for subject in subjects:
        valueLeft[subject] = dict()
        valueRight[subject] = dict()
        trials = distLeft[subject].keys()
        for trial in trials:
            valueLeft[subject][trial] = np.absolute((np.absolute(
                distLeft[subject][trial])-15)/5)
            valueRight[subject][trial] = np.absolute((np.absolute(
                distRight[subject][trial])-15)/5)

    NLL = run_analysis(rt, choice, valueLeft, valueRight, fixItem, fixTime, d,
        theta, std)

    print("d: " + str(d))
    print("theta: " + str(theta))
    print("std: " + str(std))
    print("NLL: " + str(NLL))


if __name__ == '__main__':
    main(sys.argv[1:])
