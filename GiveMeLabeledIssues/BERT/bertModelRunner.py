from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize 
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import CountVectorizer
from os import path
from sklearn.metrics import hamming_loss, accuracy_score, roc_curve, auc, roc_auc_score, f1_score, multilabel_confusion_matrix, precision_recall_fscore_support
import pandas as pd
import numpy as np
import torch

#import apex
from fast_bert.prediction import BertClassificationPredictor

from GiveMeLabeledIssues.BERT.databaseUtils import persistToDB
from GiveMeLabeledIssues.models import *

#Extractor import
from OSLextractor.extractor_driver import get_user_cfg
from OSLextractor.repo_extractor import conf, schema
from OSLextractor.repo_extractor.extractor import github_extractor
from OSLextractor.repo_extractor.utils import file_io_utils as file_io

MODEL_PATH = '/mnt/e/RESEARCH/GRAD/GiveMeLabeledIssuesAPI/GiveMeLabeledIssues/BERT/output/model_out/'
MINING_PATH = '/mnt/e/RESEARCH/GRAD/GiveMeLabeledIssuesAPI/OSLextractor/docs/example_io/example_cfg.json'

print("Model path local: " + MODEL_PATH)
print("Mining config path local: " + MINING_PATH)

#Testing limit on number of issues classified.
issueLimit = 10
threshold = .5

def filterLabels(issueLabels):
    labelStr = ""
    i = 0
    for label in issueLabels:
       # print(label)
        if label[1] >= threshold:
            labelStr += label[0]
            if i != len(issueLabels) - 1 and issueLabels[i + 1][1] >= threshold:
                labelStr += ','
        i += 1
    return labelStr

def verifyLabels(labelStr, domains):
    for domainLabel in domains:
        if domainLabel in labelStr:
            return True
    return False

def predictCombinedProjLabels(texts):
    print("Running Bert with all model for test endpoint.")
    LABEL_PATH = '/mnt/e/RESEARCH/GRAD/GiveMeLabeledIssuesAPI/GiveMeLabeledIssues/BERT/labels/all/'
    print(LABEL_PATH)
    
    predictor = BertClassificationPredictor(
                model_path=MODEL_PATH,
                label_path=LABEL_PATH, # location for labels.csv file
                multi_label=True,
                model_type='bert',
                do_lower_case=False,
                device=None) # set custom torch.device, defaults to cuda if available

    multiple_predictions = predictor.predict_batch(texts)
    return multiple_predictions
    
def buildIssueArrays(issuesDict):
    issueNums = list(issuesDict.keys())
    issueTexts = []
    issueTitles = []
    index = 0
    print("ISSUESDict: ", issuesDict)
    for issueNum in issueNums:
        issueTexts.append(issuesDict[issueNum]["body"] + issuesDict[issueNum]["title"])
        issueTitles.append(issuesDict[issueNum]["title"])
        index += 1
        if index == issueLimit:
            break
    
    return issueNums, issueTexts, issueTitles
    

def findIssues(project, labels):
    print("Running Bert with all model.")
    LABEL_PATH = '/mnt/e/RESEARCH/GRAD/GiveMeLabeledIssuesAPI/GiveMeLabeledIssues/BERT/labels/all/'
    labelsDict = {}
    projectQs = []
    issues = []
    requestVals = {"issues": []}

    if project == "JabRef/jabref":
        projectQs = JabRefIssue.objects.filter(issueLabels__contains=labels[0])

        for label in labels:
            currQs = JabRefIssue.objects.filter(issueLabels__contains=label)
            projectQs.intersection(currQs, projectQs)

        for issue in projectQs:
            print(issue.issueText)

        
    elif project == "microsoft/PowerToys":
        projectQs = PowerToysIssue.objects.filter(issueLabels__contains=labels[0])

        for label in labels:
            currQs = PowerToysIssue.objects.filter(issueLabels__contains=label)
            projectQs.intersection(currQs, projectQs)

    i = 0
    
    for issue in projectQs:
        print("ISSUE: ", i)        
        labelStr = issue.issueLabels
        issueDict = {}
        issueDict["issueTitle"] = issue.issueTitle
        issueDict["issueNumber"] = issue.issueNumber
        issueDict["issueText"] = issue.issueText
        issueDict["issueLabels"] = labelStr
        requestVals["issues"].append(issueDict)
    return requestVals

def runBertPredictions(proj_name):
    if(proj_name == "all"):
        predictCombinedProjLabels()



