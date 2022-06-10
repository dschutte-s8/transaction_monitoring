"""
Class wrapper for DGLGraph to facilitate temporal data
This is experimental and may not remain

The current thought is to parse the AMLSim graph into a collection
of timesteps and initialize the graph at t=0. Calling a step() method
will perform t+=1 and will update the balance and
add the transaction to the graph. A memory will be present should we
want to look at things in chunks such as weeks/months/etc

Thoughts:
    Integrate memory into TMGraph or keep it separate

TODO:
*    Update transaction_ledger related code to use the TransactionLedger
        class
    Incorporate transaction_ledger indexing with dates
"""

import sys
from collections import deque
from copy import deepcopy
from typing import (Union, Mapping,
                    List, Dict,
                    Optional
                   )
from warnings import warn

import torch
from torch import Tensor

from dgl import DGLGraph

from utils.data import TransactionLedger


###########
# GLOBALS #
###########

VALID_KEYS = TransactionLedger().valid_keys


#########
# FUNCS #
#########

def check_is_graph(obj):
    msg = "Attempted to pass an object that is not a DGLGraph"
    assert isinstance(obj, DGLGraph), msg


###########
# CLASSES #
###########

class Memory(deque):
    """
    Class wrapper for deque container to facilitate the use of
        DGL graphs with type checking and other conveniences
    """
    def to(self, device):
        for g in super():
            g.to(device)

    def append(self, obj):
        check_is_graph(obj)
        super().append(obj)

    def appendleft(self, obj):
        check_is_graph(obj)
        super().appendleft(obj)

    def extend(self, iterable):
        for i in iterable:
            check_is_graph(i)
        super().extend(iterable)

    def extendleft(self, iterable):
        for i in iterable:
            check_is_graph(i)
        super().extendleft(iterable)

    def insert(self, idx, obj):
        for i in iterable:
            check_is_graph(i)
        super().insert(idx, obj)


class TMGraph:
    """
    Container for AMLSim transaction graphs that allows for transactions for a
        particular timestep to be applied, account balances updated, and other
        useful functions.
    """
    def __init__(self,
                 transaction_graph: DGLGraph,
                 transaction_ledger: TransactionLedger = None,
                 backup_initial: bool = True
                ):
        self.transaction_graph = transaction_graph
        self.transaction_ledger = transaction_ledger

        self.t = 0

        self.init_trxn_graph_bak = None
        if backup_initial:
            self._backup_initial_graph()

    def step(self,
             transactions: Optional[Dict[str, Tensor]] = None
            ):
        """
        Advances the transaction graph one timestep using either the
            transaction_ledger, if included, or the provided dictionary
            of transaction data
        """
        msg = "Provide transaction data or init with transaction ledger"
        assert transactions or self.transaction_ledger, msg

        if transactions:
            data = transactions
        elif self.transaction_ledger:
            data = self.transaction_ledger[self.t]

        self._update_account_balances(data)
        self._add_transactions_to_graph(data)
        self.t += 1

    def get_state(self, t):
        """
        Returns the entire transaction graph at the specified timestep only if
            a transaction ledger is provided.
        I'm debating the utility of a function like this...
        """
        raise NotImplementedError

        #if self.transaction_ledger:
        #    if isinstance(self.transaction_ledger, dict):
        #        return self.transaction_ledger.get(t)
        #    elif isinstance(self.transaction_ledger, list):
        #        return self.transaction_ledger[t]
        #else:
        #    raise ValueError("Transaction ledger was not provided")

    def to(self, device):
        """
        Simple call to move the entire graph and all relevant components to the
            specified device
        """
        self.graph_to(device)
        self.backup_to(device)
        self.ledger_to(device)

    def graph_to(self, device):
        self.transaction_graph.to(device)

    def backup_to(self, device):
        if self.init_trxn_graph_bak:
            self.init_trxn_graph_bak.to(device)
        else:
            warn("WARNING: Backup graph does not exist")

    def ledger_to(self, device):
        if self.transaction_ledger:
            self.transaction_ledger.to(device)
        else:
            warn("WARNING: Transaction ledger not provided")

    def reset(self):
        """
        Resets the graph to the initial graph state if backup was generated at
            instantiation with backup_initial=True
        """
        if self.init_trxn_graph_bak:
            self.transaction_graph = deepcopy(self.init_trxn_graph_bak)
            self.t = 0
        else:
            warn("WARNING: Backup graph does not exist")

    def _backup_initial_graph(self):
        self.init_trxn_graph_bak = deepcopy(self.transaction_graph)

    def _update_account_balances(self, data):
        """
        Update the balances in the transacting accounts
        """
        self.transaction_graph. \
                ndata['BALANCE'][data['SENDER_ACCOUNT_ID']] -= data['TX_AMOUNT']
        self.transaction_graph. \
                ndata['BALANCE'][data['RECEIVER_ACCOUNT_ID']] += data['TX_AMOUNT']

    def _add_transactions_to_graph(self, data):
        """
        Creates new edges in the transaction graph based on the transactions
            in the provided timestep data
        """
        edata = {k:data[k] for k in VALID_KEYS if k not in
                 ['SENDER_ACCOUNT_ID','RECEIVER_ACCOUNT_ID']
                }
        self.transaction_graph.add_edges(data['SENDER_ACCOUNT_ID'],
                                         data['RECEIVER_ACCOUNT_ID'],
                                         edata
                                        )

    def _check_transaction_dict(self, transactions):
        """
        Addition of this will depend on if a class is created
            for the transaction data at each timestep
                See TODO list in src/utils/data.py
        """
        raise NotImplementedError()
