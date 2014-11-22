#!/usr/bin/python

# dyn_prog_group_fitting.py
# Author: Gabriela Tavares, gtavares@caltech.edu

import matplotlib
matplotlib.use('Agg')

from matplotlib.backends.backend_pdf import PdfPages
from multiprocessing import Pool

import matplotlib.pyplot as plt
import numpy as np
import operator
import pandas as pd

from dyn_prog_fixations import (load_data_from_csv, analysis_per_trial,
    get_empirical_distributions, run_simulations)


def generate_choice_curve_for_data(choice, valueLeft, valueRight):
    countTotal = np.zeros(7)
    countLeftChosen = np.zeros(7)

    subjects = choice.keys()
    for subject in subjects:
        trials = choice[subject].keys()
        for trial in trials:
            valueDiff = valueLeft[subject][trial] - valueRight[subject][trial]
            idx = (valueDiff / 2) + 3
            if choice[subject][trial] == -1:  # Choice was left.
                countLeftChosen[idx] +=1
                countTotal[idx] += 1
            elif choice[subject][trial] == 1:  # Choice was right.
                countTotal[idx] += 1

    stdProbLeftChosen = np.zeros(7)
    probLeftChosen = np.zeros(7)
    for i in xrange(0,7):
        probLeftChosen[i] = countLeftChosen[i] / countTotal[i]
        stdProbLeftChosen[i] = np.sqrt((probLeftChosen[i] *
            (1 - probLeftChosen[i])) / countTotal[i])

    fig = plt.figure()
    plt.errorbar(range(-6,8,2), probLeftChosen, yerr=stdProbLeftChosen,
        label='Actual data')
    plt.xlabel('Value difference')
    plt.ylabel('P(choose left)')
    plt.legend()
    return fig


def generate_choice_curve_for_simulations(choice, valueLeft, valueRight,
    numTrials):
    countTotal = np.zeros(7)
    countLeftChosen = np.zeros(7)

    for trial in xrange(0, numTrials):
        valueDiff = valueLeft[trial] - valueRight[trial]
        idx = (valueDiff / 2) + 3
        if choice[trial] == -1:  # Choice was left.
            countLeftChosen[idx] +=1
            countTotal[idx] += 1
        elif choice[trial] == 1:  # Choice was right.
            countTotal[idx] += 1

    stdProbLeftChosen = np.zeros(7)
    probLeftChosen = np.zeros(7)
    for i in xrange(0,7):
        probLeftChosen[i] = countLeftChosen[i] / countTotal[i]
        stdProbLeftChosen[i] = np.sqrt((probLeftChosen[i] *
            (1 - probLeftChosen[i])) / countTotal[i])

    fig = plt.figure()
    plt.errorbar(range(-6,8,2), probLeftChosen, yerr=stdProbLeftChosen,
        label='Simulations')
    plt.xlabel('Value difference')
    plt.ylabel('P(choose left)')
    plt.legend()
    return fig


def generate_rt_dist_for_data(rt, valueLeft, valueRight):
    rtsPerValueDiff = dict()
    for valueDiff in xrange(-6,8,2):
        rtsPerValueDiff[valueDiff] = list()

    subjects = rt.keys()
    for subject in subjects:
        trials = rt[subject].keys()
        for trial in trials:
            valueDiff = valueLeft[subject][trial] - valueRight[subject][trial]
            rtsPerValueDiff[valueDiff].append(rt[subject][trial])

    meanRts = np.zeros(7)
    stdRts = np.zeros(7)
    for valueDiff in xrange(-6,8,2):
        idx = (valueDiff / 2) + 3
        meanRts[idx] = np.mean(np.array(rtsPerValueDiff[valueDiff]))
        stdRts[idx] = (np.std(np.array(rtsPerValueDiff[valueDiff])) /
            np.sqrt(len(rtsPerValueDiff[valueDiff])))

    fig = plt.figure()
    plt.errorbar(range(-6,8,2), meanRts, yerr=stdRts, label='Actual data')
    plt.xlabel('Value difference')
    plt.ylabel('Mean RT')
    plt.legend()
    return fig


def generate_rt_dist_for_simulations(rt, valueLeft, valueRight, numTrials):
    rtsPerValueDiff = dict()
    for valueDiff in xrange(-6,8,2):
        rtsPerValueDiff[valueDiff] = list()

    for trial in xrange(0, numTrials):
        valueDiff = valueLeft[trial] - valueRight[trial]
        rtsPerValueDiff[valueDiff].append(rt[trial])

    meanRts = np.zeros(7)
    stdRts = np.zeros(7)
    for valueDiff in xrange(-6,8,2):
        idx = (valueDiff / 2) + 3
        meanRts[idx] = np.mean(np.array(rtsPerValueDiff[valueDiff]))
        stdRts[idx] = (np.std(np.array(rtsPerValueDiff[valueDiff])) /
            np.sqrt(len(rtsPerValueDiff[valueDiff])))

    fig = plt.figure()
    plt.errorbar(range(-6,8,2), meanRts, yerr=stdRts, label='Simulations')
    plt.xlabel('Value difference')
    plt.ylabel('Mean RT')
    plt.legend()
    return fig


def save_simulations_to_csv(choice, rt, valueLeft, valueRight, fixItem,
    fixTime, numTrials):
    # Psychometric choice curve.
    countTotal = np.zeros(7)
    countLeftChosen = np.zeros(7)

    for trial in xrange(0, numTrials):
        valueDiff = valueLeft[trial] - valueRight[trial]
        idx = (valueDiff / 2) + 3
        if choice[trial] == -1:  # Choice was left.
            countLeftChosen[idx] +=1
            countTotal[idx] += 1
        elif choice[trial] == 1:  # Choice was right.
            countTotal[idx] += 1

    probLeftChosen = np.zeros(7)
    stdProbLeftChosen = np.zeros(7)
    for i in xrange(0,7):
        probLeftChosen[i] = countLeftChosen[i] / countTotal[i]
        stdProbLeftChosen[i] = np.sqrt((probLeftChosen[i] *
            (1 - probLeftChosen[i])) / countTotal[i])

    d = {'prob': probLeftChosen, 'std': stdProbLeftChosen}
    df = pd.DataFrame(d)
    df.to_csv('choices.csv', header=0, sep=',', index_col=None)

    # Reaction times.
    rtsPerValueDiff = dict()
    for valueDiff in xrange(-6,8,2):
        rtsPerValueDiff[valueDiff] = list()

    for trial in xrange(0, numTrials):
        valueDiff = valueLeft[trial] - valueRight[trial]
        rtsPerValueDiff[valueDiff].append(rt[trial])

    meanRts = np.zeros(7)
    stdRts = np.zeros(7)
    for valueDiff in xrange(-6,8,2):
        idx = (valueDiff / 2) + 3
        meanRts[idx] = np.mean(np.array(rtsPerValueDiff[valueDiff]))
        stdRts[idx] = (np.std(np.array(rtsPerValueDiff[valueDiff])) /
            np.sqrt(len(rtsPerValueDiff[valueDiff])))

    d = {'meanRt': meanRts, 'std': stdRts}
    df = pd.DataFrame(d)
    df.to_csv('rts.csv', header=0, sep=',', index_col=None)

    # Pyschometric choice curve grouped by first fixation.
    countTotalLeft = np.zeros(7)
    countLeftChosenLeft = np.zeros(7)
    countTotalRight = np.zeros(7)
    countLeftChosenRight = np.zeros(7)

    for trial in xrange(0, numTrials):
        valueDiff = valueLeft[trial] - valueRight[trial]
        idx = (valueDiff / 2) + 3
        if fixItem[trial][1] == 1:  # First item was left.
            if choice[trial] == -1:  # Choice was left.
                countLeftChosenLeft[idx] +=1
                countTotalLeft[idx] += 1
            elif choice[trial] == 1:  # Choice was right.
                countTotalLeft[idx] += 1
        if fixItem[trial][1] == 2:  # First item was right.
            if choice[trial] == -1:  # Choice was left.
                countLeftChosenRight[idx] +=1
                countTotalRight[idx] += 1
            elif choice[trial] == 1:  # Choice was right.
                countTotalRight[idx] += 1

    probLeftChosenLeft = np.zeros(7)
    stdProbLeftChosenLeft = np.zeros(7)
    probLeftChosenRight = np.zeros(7)
    stdProbLeftChosenRight = np.zeros(7)
    for i in xrange(0,7):
        probLeftChosenLeft[i] = countLeftChosenLeft[i] / countTotalLeft[i]
        stdProbLeftChosenLeft[i] = np.sqrt((probLeftChosenLeft[i] *
            (1 - probLeftChosenLeft[i])) / countTotalLeft[i])
        probLeftChosenRight[i] = countLeftChosenRight[i] / countTotalRight[i]
        stdProbLeftChosenRight[i] = np.sqrt((probLeftChosenRight[i] *
            (1 - probLeftChosenRight[i])) / countTotalRight[i])

    d = {'probLeft': probLeftChosenLeft, 'stdLeft': stdProbLeftChosenLeft,
        'probRight': probLeftChosenRight, 'stdRight': stdProbLeftChosenRight}
    df = pd.DataFrame(d)
    df.to_csv('choices_first_fix.csv', header=0, sep=',', index_col=None)

    # Pyschometric choice curve grouped by last fixation.
    countTotalLeft = np.zeros(7)
    countLeftChosenLeft = np.zeros(7)
    countTotalRight = np.zeros(7)
    countLeftChosenRight = np.zeros(7)

    for trial in xrange(0, numTrials):
        valueDiff = valueLeft[trial] - valueRight[trial]
        idx = (valueDiff / 2) + 3
        if fixItem[trial][-1] == 1:  # Last item was left.
            if choice[trial] == -1:  # Choice was left.
                countLeftChosenLeft[idx] +=1
                countTotalLeft[idx] += 1
            elif choice[trial] == 1:  # Choice was right.
                countTotalLeft[idx] += 1
        if fixItem[trial][-1] == 2:  # Last item was right.
            if choice[trial] == -1:  # Choice was left.
                countLeftChosenRight[idx] +=1
                countTotalRight[idx] += 1
            elif choice[trial] == 1:  # Choice was right.
                countTotalRight[idx] += 1

    probLeftChosenLeft = np.zeros(7)
    stdProbLeftChosenLeft = np.zeros(7)
    probLeftChosenRight = np.zeros(7)
    stdProbLeftChosenRight = np.zeros(7)
    for i in xrange(0,7):
        probLeftChosenLeft[i] = countLeftChosenLeft[i] / countTotalLeft[i]
        stdProbLeftChosenLeft[i] = np.sqrt((probLeftChosenLeft[i] *
            (1 - probLeftChosenLeft[i])) / countTotalLeft[i])
        probLeftChosenRight[i] = countLeftChosenRight[i] / countTotalRight[i]
        stdProbLeftChosenRight[i] = np.sqrt((probLeftChosenRight[i] *
            (1 - probLeftChosenRight[i])) / countTotalRight[i])

    d = {'probLeft': probLeftChosenLeft, 'stdLeft': stdProbLeftChosenLeft,
        'probRight': probLeftChosenRight, 'stdRight': stdProbLeftChosenRight}
    df = pd.DataFrame(d)
    df.to_csv('choices_last_fix.csv', header=0, sep=',', index_col=None)

    # Pyschometric choice curve grouped by longest fixation time.
    countTotalLeft = np.zeros(7)
    countLeftChosenLeft = np.zeros(7)
    countTotalRight = np.zeros(7)
    countLeftChosenRight = np.zeros(7)

    for trial in xrange(0, numTrials):
        valueDiff = valueLeft[trial] - valueRight[trial]
        idx = (valueDiff / 2) + 3

        # Get total fixation time for each item.
        fixTimeLeft = 0
        fixTimeRight = 0
        for i in xrange(0, len(fixItem[trial])):
            if fixItem[trial][i] == 1:
                fixTimeLeft += fixTime[trial][i]
            elif fixItem[trial][i] == 2:
                fixTimeRight += fixTime[trial][i]

        if fixTimeLeft >= fixTimeRight:  # Longest fixated item was left.
            if choice[trial] == -1:  # Choice was left.
                countLeftChosenLeft[idx] +=1
                countTotalLeft[idx] += 1
            elif choice[trial] == 1:  # Choice was right.
                countTotalLeft[idx] += 1
        else:  # Longest fixated item was right.
            if choice[trial] == -1:  # Choice was left.
                countLeftChosenRight[idx] +=1
                countTotalRight[idx] += 1
            elif choice[trial] == 1:  # Choice was right.
                countTotalRight[idx] += 1

    probLeftChosenLeft = np.zeros(7)
    stdProbLeftChosenLeft = np.zeros(7)
    probLeftChosenRight = np.zeros(7)
    stdProbLeftChosenRight = np.zeros(7)
    for i in xrange(0,7):
        probLeftChosenLeft[i] = countLeftChosenLeft[i] / countTotalLeft[i]
        stdProbLeftChosenLeft[i] = np.sqrt((probLeftChosenLeft[i] *
            (1 - probLeftChosenLeft[i])) / countTotalLeft[i])
        probLeftChosenRight[i] = countLeftChosenRight[i] / countTotalRight[i]
        stdProbLeftChosenRight[i] = np.sqrt((probLeftChosenRight[i] *
            (1 - probLeftChosenRight[i])) / countTotalRight[i])

    d = {'probLeft': probLeftChosenLeft, 'stdLeft': stdProbLeftChosenLeft,
        'probRight': probLeftChosenRight, 'stdRight': stdProbLeftChosenRight}
    df = pd.DataFrame(d)
    df.to_csv('choices_most_fix.csv', header=0, sep=',', index_col=None)


def run_analysis(rt, choice, valueLeft, valueRight, fixItem, fixTime, d, theta,
    mu, useOddTrials=True, useEvenTrials=True, verbose=True):
    trialsPerSubject = 200
    logLikelihood = 0
    subjects = rt.keys()
    for subject in subjects:
        if verbose:
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
                fixTime[subject][trial], d, theta, mu, plotResults=False)
            if likelihood != 0:
                logLikelihood += np.log(likelihood)

    if verbose:
        print("Log likelihood for " + str(d) + ", " + str(theta) + ", "
            + str(mu) + ": " + str(logLikelihood))
    return logLikelihood


def run_analysis_wrapper(params):
    return run_analysis(*params)


def main():
    numThreads = 9
    pool = Pool(numThreads)

    # Load experimental data from CSV file.
    data = load_data_from_csv()
    rt = data.rt
    choice = data.choice
    valueLeft = data.valueLeft
    valueRight = data.valueRight
    fixItem = data.fixItem
    fixTime = data.fixTime

    # Maximum likelihood estimation using odd trials only.
    # Coarse grid search on the parameters of the model.
    print("Starting coarse grid search...")
    rangeD = [0.0002, 0.0005, 0.0008]
    rangeTheta = [0.3, 0.5, 0.7]
    rangeMu = [100, 300, 500]

    models = list()
    listParams = list()
    modelLikelihoods = dict()
    modelLikelihoods['d'] = list()
    modelLikelihoods['theta'] = list()
    modelLikelihoods['mu'] = list()
    for d in rangeD:
        for theta in rangeTheta:
            for mu in rangeMu:
                modelLikelihoods['d'].append(d)
                modelLikelihoods['theta'].append(theta)
                modelLikelihoods['mu'].append(mu)
                models.append((d, theta, mu))
                params = (rt, choice, valueLeft, valueRight, fixItem, fixTime,
                    d, theta, mu, True, False)
                listParams.append(params)

    print("Starting pool of workers...")
    resultsCoarse = pool.map(run_analysis_wrapper, listParams)

    # Get optimal parameters.
    maxLikelihoodIdx = resultsCoarse.index(max(resultsCoarse))
    optimD = models[maxLikelihoodIdx][0]
    optimTheta = models[maxLikelihoodIdx][1]
    optimMu = models[maxLikelihoodIdx][2]
    print("Finished coarse grid search!")
    print("Optimal d: " + str(optimD))
    print("Optimal theta: " + str(optimTheta))
    print("Optimal mu: " + str(optimMu))

    # Save coarse grid search results to CSV file.
    modelLikelihoods['L'] = resultsCoarse
    df = pd.DataFrame(modelLikelihoods)
    df.to_csv('likelihood_coarse.csv', header=0, sep=',', index_col=None)

    # Fine grid search on the parameters of the model.
    print("Starting fine grid search...")
    rangeD = [optimD-0.000025, optimD, optimD+0.000025]
    rangeTheta = [optimTheta-0.1, optimTheta, optimTheta+0.1]
    rangeMu = [optimMu-10, optimMu, optimMu+10]

    models = list()
    listParams = list()
    modelLikelihoods = dict()
    modelLikelihoods['d'] = list()
    modelLikelihoods['theta'] = list()
    modelLikelihoods['mu'] = list()
    for d in rangeD:
        for theta in rangeTheta:
            for mu in rangeMu:
                modelLikelihoods['d'].append(d)
                modelLikelihoods['theta'].append(theta)
                modelLikelihoods['mu'].append(mu)
                models.append((d, theta, mu))
                params = (rt, choice, valueLeft, valueRight, fixItem, fixTime,
                    d, theta, mu, True, False)
                listParams.append(params)

    print("Starting pool of workers...")
    resultsFine = pool.map(run_analysis_wrapper, listParams)

    # Get optimal parameters.
    maxLikelihoodIdx = resultsFine.index(max(resultsFine))
    optimD = models[maxLikelihoodIdx][0]
    optimTheta = models[maxLikelihoodIdx][1]
    optimMu = models[maxLikelihoodIdx][2]
    print("Finished fine grid search!")
    print("Optimal d: " + str(optimD))
    print("Optimal theta: " + str(optimTheta))
    print("Optimal mu: " + str(optimMu))

    # Save fine grid search results to CSV file.
    modelLikelihoods['L'] = resultsFine
    df = pd.DataFrame(modelLikelihoods)
    df.to_csv('likelihood_fine.csv', header=0, sep=',', index_col=None)

    # Get empirical distributions from even trials.
    even_dists = get_empirical_distributions(rt, choice, valueLeft, valueRight,
        fixItem, fixTime, useOddTrials=False, useEvenTrials=True)
    probLeftFixFirst = even_dists.probLeftFixFirst
    distTransition = even_dists.distTransition
    distFirstFix = even_dists.distFirstFix
    distMiddleFix = even_dists.distMiddleFix

    # Parameters for generating simulations.
    numTrials = 1000
    orientations = range(-15,20,5)
    trialConditions = list()
    for oLeft in orientations:
        for oRight in orientations:
            if oLeft != oRight:
                trialConditions.append((oLeft, oRight))

    # Generate simulations using the even trials distributions and the
    # estimated parameters.
    simul = run_simulations(numTrials, trialConditions, optimD, optimTheta,
        optimMu, probLeftFixFirst, distTransition, distFirstFix, distMiddleFix)
    simulRt = simul.rt
    simulChoice = simul.choice
    simulValueLeft = simul.valueLeft
    simulValueRight = simul.valueRight
    simulFixItem = simul.fixItem
    simulFixTime = simul.fixTime

    # Create pdf file to save figures.
    pp = PdfPages("figures_" + str(optimD) + "_" + str(optimTheta) + "_" +
        str(optimMu) + "_" + str(numTrials) + ".pdf")

    # Generate histograms and choice curves for real data (odd trials) and
    # simulations (generated from even trials).
    fig1 = generate_choice_curve_for_data(choice, valueLeft, valueRight)
    pp.savefig(fig1)
    fig2 = generate_rt_dist_for_data(rt, valueLeft, valueRight)
    pp.savefig(fig2)

    totalTrials = numTrials * len(trialConditions)
    fig3 = generate_choice_curve_for_simulations(simulChoice, simulValueLeft,
        simulValueRight, totalTrials)
    pp.savefig(fig3)
    fig4 = generate_rt_dist_for_simulations(simulRt, simulValueLeft,
        simulValueRight, totalTrials)
    pp.savefig(fig4)
    pp.close()

    save_simulations_to_csv(simulChoice, simulRt, simulValueLeft,
        simulValueRight, simulFixItem, simulFixTime, totalTrials)


if __name__ == '__main__':
    main()