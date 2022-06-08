"""
Class to simplify data loading, storage, and use

TODO:
    Add S3 data loading function
    Add handling of temporal data (interval algebra)
    Convert to using heterograph
    Add edge type OWNS_ACCOUNT & OWNS_ACCOUNT^-1 using customer_account dict
    More to come...
"""

import os
from time import time
from dataclasses import dataclass

from boto3 import resource

from pandas import read_csv

import torch

from dgl import graph


###########
# GLOBALS #
###########



#########
# FUNCS #
#########


def get_aml_data_s3(bucket, data_path):
    """
    Retrieves the data from the specified S3 bucket and
        loads it into a AMLData object and DGL graph
    ARGS:
        bucket(str):= name of S3 bucket containing data
        data_path(str):= path to AMLSim data
    RETURNS:
        (AMLData object, DGL Graph)
    """
    raise NotImplementedError("Work in progress!")


def get_aml_graph_local(data_path):
    """
    Loads the AMLSim graph into an AMLData object
        and a DGL graph
    ARGS:
        data_path(str): path to the AMLSim data
    RETURNS:
        (AMLData object, DGL Graph)
    """
    assert os.path.isdir(data_path), "Provided data_path is not a directory"
    print("Loading data...")
    aml_data = AMLData(data_dir=data_path)
    aml_data.load_data()
    print("Preparing graph object...")
    nodes_u, nodes_v, node_feats, edge_feats = aml_data.prep_data_for_graph()
    G = graph((nodes_u, nodes_v))
    G.ndata['INIT_BALANCE'] = node_feats['INIT_BALANCE']
    G.ndata['COUNTRY'] = node_feats['COUNTRY']
    G.ndata['ACCOUNT_TYPE'] = node_feats['ACCOUNT_TYPE']
    G.edata['TX_AMOUNT'] = edge_feats['TX_AMOUNT']
    G.edata['TIMESTAMP'] = edge_feats['TIMESTAMP']
    G.edata['TX_TYPE'] = edge_feats['TX_TYPE']
    print("Graph created!")
    return aml_data, G


###########
# CLASSES #
###########

class AMLData:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.accounts_path = os.path.join(data_dir, 'accounts.csv')
        self.transactions_path = os.path.join(data_dir, 'transactions.csv')
        self.alerts_path = os.path.join(data_dir, 'alerts.csv')
        self.customer_accounts = self.account2customer = "Run AMLData.agg_customer_accounts() to generate these dictionaries"

    def load_data(self):
        start = time()
        self.accounts = read_csv(self.accounts_path)
        self.transactions = read_csv(self.transactions_path)
        self.alerts = read_csv(self.alerts_path)
        end = time() - start

        msg = "Loaded:\n\t"
        msg += f"{len(self.accounts)} accounts"+"\n\t"
        msg += f"{len(self.transactions)} transactions"+"\n\t"
        msg += f"{len(self.alerts)} alerts"+"\n\t"
        msg += f"Loaded in: {round(end,4)}s"

        print(msg)

    def prep_data_for_graph(self):
        """
        Prepares the data to be loaded into a graph object. DGL
            requires all data be numeric.
        RETURNS:
            nodes_u: origin nodes
            nodes_v: destination nodes
            node_feats: node features in dict
            edge feats: edge features in dict
        """
        self._make_data_dicts()
        nodes_u = torch.tensor(self.transactions['SENDER_ACCOUNT_ID'].values)
        nodes_v = torch.tensor(self.transactions['RECEIVER_ACCOUNT_ID'].values)
        node_feats = {'INIT_BALANCE': torch.tensor(self.accounts.INIT_BALANCE),
                      'COUNTRY': torch.tensor(self.accounts.COUNTRY \
                        .replace(self.data_dicts['country2id'])),
                      'ACCOUNT_TYPE': torch.tensor(self.accounts.ACCOUNT_TYPE \
                        .replace(self.data_dicts['acct_type2id'])),
                     }
        edge_feats = {'TX_AMOUNT': torch.tensor(self.transactions.TX_AMOUNT),
                      'TIMESTAMP': torch.tensor(self.transactions.TIMESTAMP),
                      'TX_TYPE': torch.tensor(self.transactions.TX_TYPE \
                        .replace(self.data_dicts['trxn_type2id'])),
                     }

        return nodes_u, nodes_v, node_feats, edge_feats


    def _make_data_dicts(self):
        """
        Generates dicts to convert non-numeric values (e.g. transaction type,
            country) to integer values
        """
        # Map countries
        country2id = {c:i for i, c in enumerate(set(self.accounts.COUNTRY.values))}
        id2country = {i:c for c, i in country2id.items()}
        # Map account type
        acct_type2id = {a:i for i, a in enumerate(set(self.accounts.ACCOUNT_TYPE.values))}
        id2acct_type = {i:a for a, i in acct_type2id.items()}
        # Map transaction type
        trxn_type2id = {t:i for i, t in enumerate(set(self.transactions.TX_TYPE.values))}
        id2trxn_type = {i:t for t, i in trxn_type2id.items()}

        self.data_dicts = {'country2id': country2id,
                           'id2country': id2country,
                           'acct_type2id': acct_type2id,
                           'id2acct_type': id2acct_type,
                           'trxn_type2id': trxn_type2id,
                           'id2trxn_type': id2trxn_type
                          }

    def agg_customer_accounts(self):
        """
        Creates dictionaries that associates all accounts associated with a
            particular customer and vice versa
        """
        self.customer_accounts = {c: self.accounts[self.accounts.CUSTOMER_ID==c]
                                  for c in set(self.accounts.CUSTOMER_ID.values)
                                 }
        self.account2customer = {a:c for a,c in zip(self.accounts.ACCOUNT_ID,
                                                    self.accounts.CUSTOMER_ID
                                                   )
                                }
