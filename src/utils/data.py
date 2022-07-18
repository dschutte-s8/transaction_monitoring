"""
Class to simplify data loading, storage, and use

TODO (no particular order):
    Add S3 data loading function
*    Add validation of transaction dicts
*    |-> TransactionLedger might be best as a class of its own...
     |-> class for easy validation of data at each timestep?
    Add handling of temporal data (interval algebra)
    |-> I think using a RL-env inspired setup might be the way to go...
     |-> WIP in src/tmgraph.py
    Enable using heterograph
    Add edge type OWNS_ACCOUNT & OWNS_ACCOUNT^-1 using customer_account dict
    More to come...
"""

import os
from time import time

from boto3 import resource

from pandas import read_csv

import torch
from torch import tensor

from dgl import graph, DGLGraph


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


def get_aml_graph_local(data_path: str,
                        load_all_trxns_into_graph: bool = False,
                        ):
    """
    Loads the AMLSim graph into an AMLData object
        and a DGL graph
    ARGS:
        data_path(str):= path to the AMLSim data
        load_all_trxns_into_graph(bool):= load all transactions into the graph
            if True, else prodcue a transaction ledger for downstream use
    RETURNS:
        (AMLData object, DGL Graph)
    """
    assert os.path.isdir(data_path), "Provided data_path is not a directory"
    print("Loading data...")
    aml_data = AMLData(data_dir=data_path)
    aml_data.load_data()
    print("Preparing graph object...")
    nodes_u, nodes_v, node_feats, edge_feats = aml_data.prep_data_for_graph()
    if load_all_trxns_into_graph:
        G = graph((nodes_u, nodes_v))
        G.ndata['BALANCE'] = node_feats['BALANCE']
        G.ndata['COUNTRY'] = node_feats['COUNTRY']
        G.ndata['ACCOUNT_TYPE'] = node_feats['ACCOUNT_TYPE']
        print("Graph created...")
        print("Loading all transactions into graph...")
        G.edata['TX_AMOUNT'] = edge_feats['TX_AMOUNT']
        G.edata['TIMESTAMP'] = edge_feats['TIMESTAMP']
        G.edata['TX_TYPE'] = edge_feats['TX_TYPE']
    else:
        # Raises a warning, find better solution
        G = DGLGraph()
        G.add_nodes(len(aml_data.accounts),
                    {'BALANCE': node_feats['BALANCE'],
                     'COUNTRY': node_feats['COUNTRY'],
                     'ACCOUNT_TYPE': node_feats['ACCOUNT_TYPE']
                    }
                   )
        print("Graph created...")
        print("Building transaction ledger...")
        ledger = aml_data.make_transaction_ledger()
    return aml_data, G


###########
# CLASSES #
###########

class TransactionLedger(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.valid_keys = set(['TX_ID',
                               'SENDER_ACCOUNT_ID',
                               'RECEIVER_ACCOUNT_ID',
                               'TX_AMOUNT',
                               'TIMESTAMP',
                               'TX_TYPE'
                              ]
                             )

    def _validate_addition(self, key, mapping):
        assert isinstance(key, int), "ledger keys must be integers for now"
        assert self.valid_keys == set(mapping.keys())
        assert all([isinstance(v, torch.Tensor) for v in mapping.values()])

    def update(self, mapping):
        for k, v in mapping.items():
            self._validate_addition(k, v)
            self[k] = v

    def to(self, device):
        """
        This could be enabled here or device stored and objects moved
            when an object is retreived
        """
        raise NotImplementedError("Deciding on best approach")


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
        node_feats = {'BALANCE': torch.tensor(self.accounts.INIT_BALANCE),
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

    def make_transaction_ledger(self):
        """
        Partitions the transaction data into a dictionary or list where each
            entry is all the data for a particular timestep
        """
        timestamps = set(self.transactions.TIMESTAMP.astype(int).values)
        self.ledger = TransactionLedger()
        for t in timestamps:
            t = int(t)
            tmp = self.transactions[self.transactions.TIMESTAMP==t]
            tmp.iloc[:]['TX_TYPE'].replace(self.data_dicts['trxn_type2id'],
                                   inplace=True
                                  )
            transactions_t = {'TX_ID':tmp.TX_ID.astype(int).values,
                              'SENDER_ACCOUNT_ID': tmp.SENDER_ACCOUNT_ID. \
                                    astype(int).values,
                              'RECEIVER_ACCOUNT_ID':tmp.RECEIVER_ACCOUNT_ID. \
                                    astype(int).values,
                              'TX_TYPE':tmp.TX_TYPE.astype(int).values,
                              'TX_AMOUNT':tmp.TX_AMOUNT.astype(float).values,
                              'TIMESTAMP':tmp.TIMESTAMP.astype(int).values
                             }
            transactions_t = {k:tensor(v) for k,v in transactions_t.items()}
            self.ledger.update({t: transactions_t})
