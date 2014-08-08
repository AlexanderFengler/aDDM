#!/usr/bin/python

# dyn_prog_fixations.py
# Author: Gabriela Tavares, gtavares@caltech.edu

from multiprocessing import Pool
from numba import jit
from scipy.stats import norm

import collections
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import error_report


def load_data_from_csv():
    # Load experimental data from CSV file.
    # Format: parcode, trial, rt, choice, dist_left, dist_right.
    df = pd.DataFrame.from_csv('expdata.csv', header=0, sep=',', index_col=None)
    subjects = df.parcode.unique()

    rt = dict()
    choice = dict()
    valueLeft = dict()
    valueRight = dict() 

    for subject in subjects:
        rt[subject] = dict()
        choice[subject] = dict()
        valueLeft[subject] = dict()
        valueRight[subject] = dict()
        dataSubject = np.array(df.loc[df['parcode']==subject,
            ['trial','rt','choice','dist_left','dist_right']])
        trials = np.unique(dataSubject[:,0]).tolist()
        for trial in trials:
            dataTrial = np.array(df.loc[(df['trial']==trial) &
                (df['parcode']==subject), ['rt','choice','dist_left',
                'dist_right']])
            rt[subject][trial] = dataTrial[0,0]
            choice[subject][trial] = dataTrial[0,1]
            valueLeft[subject][trial] = np.absolute(
                (np.absolute(dataTrial[0,2])-15)/5)
            valueRight[subject][trial] = np.absolute(
                (np.absolute(dataTrial[0,3])-15)/5)

    # Load fixation data from CSV file.
    # Format: parcode, trial, fix_item, fix_time.
    df = pd.DataFrame.from_csv('fixations.csv', header=0, sep=',',
        index_col=None)
    subjects = df.parcode.unique()

    fixItem = dict()
    fixTime = dict()

    for subject in subjects:
        fixItem[subject] = dict()
        fixTime[subject] = dict()
        dataSubject = np.array(df.loc[df['parcode']==subject,
            ['trial','fix_item','fix_time']])
        trials = np.unique(dataSubject[:,0]).tolist()
        for trial in trials:
            dataTrial = np.array(df.loc[(df['trial']==trial) &
                (df['parcode']==subject), ['fix_item','fix_time']])
            fixItem[subject][trial] = dataTrial[:,0]
            fixTime[subject][trial] = dataTrial[:,1]

    data = collections.namedtuple('Data', ['rt', 'choice', 'valueLeft',
        'valueRight', 'fixItem', 'fixTime'])
    return data(rt, choice, valueLeft, valueRight, fixItem, fixTime)


# @jit("(f8,f8,f8,f8,f8[:],f8[:],f8,f8,f8)")
def analysis_per_trial(rt, choice, valueLeft, valueRight, fixItem, fixTime, d,
    theta, std, log):
    # Parameters of the grid.
    stateStep = 0.1
    timeStep = 1
    initialBarrierUp = 1
    initialBarrierDown = -1

    # Iterate over the fixations and get the transition time for this trial.
    itemFixTime = 0
    transitionTime = 0
    for fItem, fTime in zip(fixItem, fixTime):
        if fItem == 1 or fItem == 2:
            itemFixTime += fTime // timeStep
        else:
            transitionTime += fTime // timeStep

    # The total time of this trial is given by the sum of all fixations
    # in the trial.
    maxTime = itemFixTime + transitionTime

    # We start couting the trial time at the end of the transition time.
    time = transitionTime

    # The values of the barriers can change over time.
    decay = 0  # decay = 0 means barriers are constant.
    barrierUp = initialBarrierUp * np.ones(maxTime)
    barrierDown = initialBarrierDown * np.ones(maxTime)
    for t in xrange(0, int(maxTime)):
        barrierUp[t] = float(initialBarrierUp) / float(1+decay*(t+1))
        barrierDown[t] = float(initialBarrierDown) / float(1+decay*(t+1))

    # The vertical axis is divided into states.
    states = np.arange(initialBarrierDown + stateStep, initialBarrierUp,
        stateStep)
    idx = np.where(np.logical_and(states<0.01, states>-0.01))[0]
    states[idx] = 0

    # Initial probability for all states is zero, except for the zero state,
    # which has initial probability equal to one.
    prStates = np.zeros(states.size)
    idx = np.where(states==0)[0]
    prStates[idx] = 1

    # The probability of crossing each barrier over the time of the trial.
    probUpCrossing = np.zeros(maxTime)
    probDownCrossing = np.zeros(maxTime)

    # Iterate over all fixations in this trial.
    for fItem, fTime in zip(fixItem, fixTime):
        # We use a distribution to model changes in RDV stochastically. The mean
        # of the distribution (the change most likely to occur) is calculated
        # from the model parameters and from the values of the two items.
        if fItem == 1:  # subject is looking left.
            mean = d * (valueLeft - (theta * valueRight))
        elif fItem == 2:  # subject is looking right.
            mean = d * (-valueRight + (theta * valueLeft))
        else:
            continue

        # Iterate over the time interval of this fixation.
        for t in xrange(0, int(fTime // timeStep)):
            log.write_message("Time: " + str(time))
            log.write_message(str(prStates))

            prStatesNew = np.zeros(states.size)

            # Update the probability of the states that remain inside the
            # barriers.
            for s in xrange(0, states.size):
                currState = states[s]
                if (currState > barrierDown[time] and
                    currState < barrierUp[time]):
                    change = (currState * np.ones(states.size)) - states
                    # The probability of being in state B is the sum, over all
                    # states A, of the probability of being in A at the previous
                    # timestep times the probability of changing from A to B.
                    prStatesNew[s] = (stateStep * np.sum(np.multiply(prStates,
                        norm.pdf(change,mean,std))))

            # Calculate the probabilities of crossing the up barrier and the
            # down barrier. This is given by the sum, over all states A, of the
            # probability of being in A at the previous timestep times the
            # probability of crossing the barrier if A is the previous state.
            changeUp = (barrierUp[time] * np.ones(states.size)) - states
            tempUpCross = np.sum(np.multiply(prStates,
                (1 - norm.cdf(changeUp,mean,std))))
            changeDown = (barrierDown[time] * np.ones(states.size)) - states
            tempDownCross = np.sum(np.multiply(prStates,
                (norm.cdf(changeDown,mean,std))))

            # log.write_message("mean: " + str(mean))
            # log.write_message("std: " + str(std))
            # log.write_message("cdf UP")
            # log.write_message(norm.cdf(changeUp,mean,std))
            # log.write_message("cdf DOWN")
            # log.write_message(norm.cdf(changeDown,mean,std))

            # Renormalize to cope with numerical approximations.
            sumIn = np.sum(prStates)
            sumCurrent = np.sum(prStatesNew) + tempUpCross + tempDownCross
            prStatesNew = (prStatesNew * float(sumIn)) / float(sumCurrent)
            tempUpCross = (tempUpCross * float(sumIn)) / float(sumCurrent)
            tempDownCross = (tempDownCross * float(sumIn)) / float(sumCurrent)

            # Update the probabilities of each state and the probabilities of
            # crossing each barrier at this timestep.
            prStates = prStatesNew
            probUpCrossing[time] = tempUpCross
            probDownCrossing[time] = tempDownCross

            time += 1

    log.write_message("PROB UP CROSSING: ")
    log.write_message(str(probUpCrossing))
    log.write_message("PROB DOWN CROSSING: ")
    log.write_message(str(probDownCrossing))

    # Compute the log likelihood contribution of this trial based on the final
    # choice.
    likelihood = 0
    if choice == -1:  # choice was left.
        if probUpCrossing[-1] > 0:
            likelihood = np.log(probUpCrossing[-1])
    elif choice == 1:  # choice was right.
        if probDownCrossing[-1] > 0:
            likelihood = np.log(probDownCrossing[-1])

    log.write_message("LIKELIHOOD: " + str(likelihood))
    return likelihood


def run_analysis(rt, choice, valueLeft, valueRight, fixItem, fixTime, d, theta,
    std):
    likelihood = 0
    subjects = rt.keys()
    for subject in subjects:
        print("Running subject " + subject + "...")
        trials = rt[subject].keys()
        for trial in trials:
            if trial % 200 == 0:
                print("Trial " + str(trial))
            likelihood += analysis_per_trial(rt[subject][trial],
                choice[subject][trial], valueLeft[subject][trial],
                valueRight[subject][trial], fixItem[subject][trial],
                fixTime[subject][trial], d, theta, std)

    print("Likelihood: " + str(likelihood))
    return likelihood


def run_analysis_wrapper(params):
    return run_analysis(*params)


def main():
    numThreads = 4
    pool = Pool(numThreads)

    data = load_data_from_csv()
    rt = data.rt
    choice = data.choice
    valueLeft = data.valueLeft
    valueRight = data.valueRight
    fixItem = data.fixItem
    fixTime = data.fixTime

    # Coarse grid search on the parameters of the model.
    print("Starting coarse grid search...")
    rangeD = [0.0015, 0.002, 0.0025]
    rangeTheta = [0.5, 0.7, 0.9]
    rangeStd = [0.15, 0.2, 0.25]

    models = list()
    list_params = list()
    for d in rangeD:
        for theta in rangeTheta:
            for std in rangeStd:
                models.append((d, theta, std))
                params = (rt, choice, valueLeft, valueRight, fixItem, fixTime,
                    d, theta, std)
                list_params.append(params)

    print("Starting pool of workers...")
    results_coarse = pool.map(run_analysis_wrapper, list_params)

    # Get optimal parameters.
    max_likelihood_idx = results_coarse.index(max(results_coarse))
    optimD = models[max_likelihood_idx][0]
    optimTheta = models[max_likelihood_idx][1]
    optimStd = models[max_likelihood_idx][2]
    print("Finished coarse grid search!")
    print("Optimal d: " + str(optimD))
    print("Optimal theta: " + str(optimTheta))
    print("Optimal std: " + str(optimStd))

    # Fine grid search on the parameters of the model.
    print("Starting fine grid search...")
    rangeD = [optimD-0.00025, optimD, optimD+0.00025]
    rangeTheta = [optimTheta-0.1, optimTheta, optimTheta+0.1]
    rangeStd = [optimStd-0.025, optimStd, optimStd+0.025]

    models = list()
    list_params = list()
    for d in rangeD:
        for theta in rangeTheta:
            for std in rangeStd:
                models.append((d, theta, std))
                params = (rt, choice, valueLeft, valueRight, fixItem, fixTime,
                    d, theta, std)
                list_params.append(params)

    print("Starting pool of workers...")
    results_fine = pool.map(run_analysis_wrapper, list_params)

    # Get optimal parameters.
    max_likelihood_idx = results_fine.index(max(results_fine))
    optimD = models[max_likelihood_idx][0]
    optimTheta = models[max_likelihood_idx][1]
    optimStd = models[max_likelihood_idx][2]
    print("Finished fine grid search!")
    print("Optimal d: " + str(optimD))
    print("Optimal theta: " + str(optimTheta))
    print("Optimal std: " + str(optimStd))


if __name__ == '__main__':
    main()
