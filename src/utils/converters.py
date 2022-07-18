"""
Functions to convert between graph frameworks

TODO:
    -Add function to convert TMGraph from
        dgl to torch geo (will need extra
        work as some methods in TMGraph
        are likely to break)
"""

from dgl import (DGLGraph,
                 to_homogeneous,
                 to_networkx
                )
from torch_geometric.utils import from_networkx

from tmgraph import TMGraph


#########
# FUNCS #
#########

def dgl_to_torch_geo(graph):
    """
    Converts a dgl graph to a pytorch geometric graph
    """
    msg = f"Expected DGLGraph obj got {type(graph)}"
    assert isinstance(graph, DGLGraph), msg
    interim = to_networkx(graph)
    return from_networkx(interim)


def tmgraph_to_torch_geo(tmg,
                         advance: bool = False
                        ):
    """
    Returns the transaction graph stored in the
        TMGraph object as a torch_geometric graph.
        If advance==True, the TMGraph is run to
        completion then converted.
    """
    msg = f"Expected TMGraph obj got {type(tmg)}"
    assert isinstance(tmg, TMGraph)
    if advance:
        if (tmg.t != len(tmg.transaction_ledger)):
            for i in range(len(tmg.transaction_ledger)-tmg.t):
                tmg.step()
    return dgl_to_torch_geo(tmg.transaction_graph)
