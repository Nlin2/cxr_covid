#!/usr/bin/env python
#
# train_covid.py
#
# Run ``python train_covid.py -h'' for information on using this script.
#

import os
import sys

import argparse
import numpy
import sklearn.metrics

from models import CXRClassifier
from datasets import ChestXray14H5Dataset, PadChestH5Dataset
from datasets import GitHubCOVIDDataset, BIMCVCOVIDDataset
from datasets import DomainConfoundedDataset



def _find_index(ds, desired_label):
    desired_index = None
    for ilabel, label in enumerate(ds.labels):
        if label.lower() == desired_label.lower():
            desired_index = ilabel
            break
    if not desired_index is None:
        return desired_index
    else:
        raise ValueError("Label {:s} not found.".format(desired_label))

def train_githubcxr14(seed, alexnet=False, freeze_features=False):
    trainds = DomainConfoundedDataset(
            ChestXray14H5Dataset(fold='train', labels='chestx-ray14', random_state=seed),
            GitHubCOVIDDataset(fold='train', labels='chestx-ray14', random_state=seed)
            )

    valds = DomainConfoundedDataset(
            ChestXray14H5Dataset(fold='val', labels='chestx-ray14', random_state=seed),
            GitHubCOVIDDataset(fold='val', labels='chestx-ray14', random_state=seed)
            )

    # generate log and checkpoint paths
    if alexnet: netstring = 'alexnet'
    elif freeze_features: netstring = 'densenet121frozen'
    else: netstring = 'densenet121'
    logpath = 'logs/githubcxr14.{:s}.{:d}.log'.format(netstring, seed)
    checkpointpath = 'checkpoints/githubcxr14.{:s}.{:d}.pkl'.format(netstring, seed)

    classifier = CXRClassifier()
    classifier.train(trainds,
                valds,
                max_epochs=30,
                lr=0.01, 
                weight_decay=1e-4,
                logpath=logpath,
                checkpoint_path=checkpointpath,
                verbose=True,
                scratch_train=alexnet,
                freeze_features=freeze_features)

def train_bimcvpadchest(seed, alexnet=False, freeze_features=False):
    trainds = DomainConfoundedDataset(
            PadChestH5Dataset(fold='train', labels='chestx-ray14', random_state=seed),
            BIMCVCOVIDDataset(fold='train', labels='chestx-ray14', random_state=seed)
            )
    valds = DomainConfoundedDataset(
            PadChestH5Dataset(fold='val', labels='chestx-ray14', random_state=seed),
            BIMCVCOVIDDataset(fold='val', labels='chestx-ray14', random_state=seed)
            )

    # generate log and checkpoint paths
    if alexnet: netstring = 'alexnet'
    elif freeze_features: netstring = 'densenet121frozen'
    else: netstring = 'densenet121'
    logpath = 'logs/bimcvpadchest.{:s}.{:d}.log'.format(netstring, seed)
    checkpointpath = 'checkpoints/bimcvpadchest.{:s}.{:d}.pkl'.format(netstring, seed)

    classifier = CXRClassifier()
    classifier.train(trainds,
                valds,
                max_epochs=30,
                lr=0.01, 
                weight_decay=1e-4,
                logpath=logpath,
                checkpoint_path=checkpointpath,
                verbose=True,
                scratch_train=alexnet,
                freeze_features=freeze_features)

def test_githubcxr14(seed, alexnet=False, freeze_features=False):
    internal_testds = DomainConfoundedDataset(
            ChestXray14H5Dataset(fold='test', labels='chestx-ray14', random_state=seed),
            GitHubCOVIDDataset(fold='test', labels='chestx-ray14', random_state=seed)
            )

    external_testds = DomainConfoundedDataset(
            PadChestH5Dataset(fold='test', labels='chestx-ray14', random_state=seed),
            BIMCVCOVIDDataset(fold='test', labels='chestx-ray14', random_state=seed)
            )

    # generate checkpoint path
    if alexnet: netstring = 'alexnet'
    elif freeze_features: netstring = 'densenet121frozen'
    else: netstring = 'densenet121'
    checkpointpath = 'checkpoints/githubcxr14.{:s}.{:d}.pkl.best_auroc'.format(netstring, seed)

    classifier = CXRClassifier()
    classifier.load_checkpoint(checkpointpath)
    
    internal_probs = classifier.predict(internal_testds)
    internal_true = internal_testds.get_all_labels()
    internal_idx = _find_index(internal_testds, 'COVID')
    internal_auroc = sklearn.metrics.roc_auc_score(
            internal_true[:, internal_idx],
            internal_probs[:, internal_idx]
            )
    print("internal auroc: ", internal_auroc)

    external_idx = _find_index(external_testds, 'COVID')
    external_true = external_testds.get_all_labels()
    # a little hacky here!
    external_testds.labels = internal_testds.labels
    external_probs = classifier.predict(external_testds)
    external_auroc = sklearn.metrics.roc_auc_score(
            external_true[:, external_idx],
            external_probs[:, internal_idx] # not a typo! this *should* be internal_idx
            )
    print("external auroc: ", external_auroc)

def test_bimcvpadchest(seed, alexnet=False, freeze_features=False):
    internal_testds = DomainConfoundedDataset(
            PadChestH5Dataset(fold='test', labels='chestx-ray14', random_state=seed),
            BIMCVCOVIDDataset(fold='test', labels='chestx-ray14', random_state=seed)
            )
    external_testds = DomainConfoundedDataset(
            ChestXray14H5Dataset(fold='test', labels='chestx-ray14', random_state=seed),
            GitHubCOVIDDataset(fold='test', labels='chestx-ray14', random_state=seed)
            )

    # generate checkpoint path
    if alexnet: netstring = 'alexnet'
    elif freeze_features: netstring = 'densenet121frozen'
    else: netstring = 'densenet121'
    checkpointpath = 'checkpoints/bimcvpadchest.{:s}.{:d}.pkl.best_auroc'.format(netstring, seed)

    classifier = CXRClassifier()
    classifier.load_checkpoint(checkpointpath)
    
    internal_probs = classifier.predict(internal_testds)
    internal_true = internal_testds.get_all_labels()
    internal_idx = _find_index(internal_testds, 'COVID')
    internal_auroc = sklearn.metrics.roc_auc_score(
            internal_true[:, internal_idx],
            internal_probs[:, internal_idx]
            )
    print("internal auroc: ", internal_auroc)

    external_true = external_testds.get_all_labels()
    external_idx = _find_index(external_testds, 'COVID')
    # a little hacky here!
    external_testds.labels = internal_testds.labels
    external_probs = classifier.predict(external_testds)
    external_auroc = sklearn.metrics.roc_auc_score(
            external_true[:, external_idx],
            external_probs[:, internal_idx] # not a typo! this *should* be internal_idx
            )
    print("external auroc: ", external_auroc)

def main():
    parser = argparse.ArgumentParser(description='Training script for COVID-19 '
            'classifiers. Make sure that datasets have been set up before '
            'running this script. See the README file for more information.')
    parser.add_argument('--dataset', dest='dataset', type=int, default=1, required=False,
                        help='The dataset number on which to train. Choose "1" or "2".')
    parser.add_argument('--seed', dest='seed', type=int, default=30493, required=False,
                        help='The random seed used to generate train/val/test splits')
    parser.add_argument('--network', dest='network', type=str, default='densenet121', required=False,
                        help='The network type. Choose "densenet121", "logistic", or "alexnet".')
    parser.add_argument('--device-index', dest='deviceidx', type=int, default=None, required=False,
                        help='The index of the GPU device to use. If None, use the default GPU.')
    args = parser.parse_args()

    for dirname in ['checkpoints', 'logs']:
        if not os.path.isdir(dirname):
            os.mkdir(dirname)

    if args.deviceidx is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = "{:d}".format(args.deviceidx)

    if args.dataset == 1:
        train_githubcxr14(args.seed, 
                alexnet=(args.network.lower() == 'alexnet'), 
                freeze_features=(args.network.lower() == 'logistic'))
    if args.dataset == 2:
        train_bimcvpadchest(args.seed, 
                alexnet=(args.network.lower() == 'alexnet'), 
                freeze_features=(args.network.lower() == 'logistic'))

if __name__ == "__main__":
    main()
