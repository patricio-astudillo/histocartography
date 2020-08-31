import torch
import torch.nn as nn
import importlib
import dgl

from histocartography.ml.layers.constants import (
    AVAILABLE_LAYER_TYPES, GNN_MODULE,
    GNN_NODE_FEAT_OUT, READOUT_TYPES,
    REDUCE_TYPES
)


class MultiLayerGNN(nn.Module):
    """
    MultiLayer network that concatenate several gnn layers layer
    """

    def __init__(self, config):
        """
        MultiLayer GNN constructor.
        :param config: (dict) configuration parameters. Refer to the layers implementation
                              for the parameter description.
        """
        super(MultiLayerGNN, self).__init__()

        layer_type = config['layer_type']
        if layer_type in list(AVAILABLE_LAYER_TYPES.keys()):
            module = importlib.import_module(
                GNN_MODULE.format(layer_type)
            )
        else:
            raise ValueError(
                'GNN type: {} not recognized. Options are: {}'.format(
                    layer_type, list(AVAILABLE_LAYER_TYPES.keys())
                )
            )

        self.config = config
        in_dim = config['input_dim']
        hidden_dim = config['hidden_dim']
        out_dim = config['output_dim']
        num_layers = config['n_layers']
        activation = config['activation']
        edge_dim = config['edge_dim']

        self.layers = nn.ModuleList()

        # input layer
        self.layers.append(getattr(module, AVAILABLE_LAYER_TYPES[layer_type])(
            node_dim=in_dim,
            out_dim=hidden_dim,
            act=activation,
            layer_id=0,
            config=config,
            edge_dim=edge_dim)
        )
        # hidden layers
        for i in range(1, num_layers - 1):
            self.layers.append(
                getattr(
                    module,
                    AVAILABLE_LAYER_TYPES[layer_type])(
                    node_dim=hidden_dim,
                    out_dim=hidden_dim,
                    act=activation,
                    layer_id=i,
                    config=config,
                    edge_dim=edge_dim)
                )
        # output layer
        self.layers.append(getattr(module, AVAILABLE_LAYER_TYPES[layer_type])(
            node_dim=hidden_dim,
            out_dim=out_dim,
            act=activation,
            layer_id=num_layers - 1,
            config=config,
            edge_dim=edge_dim)
        )

        # readout op
        self.readout_op = config["agg_operator"]
        if self.readout_op == "lstm":
            self.lstm = nn.LSTM(
                out_dim, (num_layers * out_dim) // 2,
                bidirectional=True,
                batch_first=True)
            self.att =nn.Linear(2 * ((num_layers * out_dim) // 2), 1)

        # readout function
        self.readout_type = config['neighbor_pooling_type'] if 'neighbor_pooling_type' in config.keys(
        ) else 'sum'

    def forward(self, g, h, with_readout=True):
        """
        Forward pass.
        :param g: (DGLGraph)
        :param h: (FloatTensor)
        :param cat: (bool) if concat the features at each conv layer
        :return:
        """
        h_concat = []
        for layer in self.layers:
            h = layer(g, h)
            h_concat.append(h)

        if isinstance(g, dgl.DGLGraph):

            # aggregate the multi-scale node representations 
            if self.readout_op == "concat":
                g.ndata[GNN_NODE_FEAT_OUT] = torch.cat(h_concat, dim=-1)
            elif self.readout_op == "lstm":
                x = torch.stack(h_concat, dim=1)  # [num_nodes, num_layers, num_channels]
                alpha, _ = self.lstm(x)
                alpha = self.att(alpha).squeeze(-1)  # [num_nodes, num_layers]
                alpha = torch.softmax(alpha, dim=-1)
                g.ndata[GNN_NODE_FEAT_OUT] = (x * alpha.unsqueeze(-1)).sum(dim=1)
            elif self.readout_op == "none":
                g.ndata[GNN_NODE_FEAT_OUT] = h
            else:
                raise ValueError("Unsupported readout operator. Options are 'concat', 'lstm', 'none'.")

            # readout
            if with_readout:
                return READOUT_TYPES[self.readout_type](g, GNN_NODE_FEAT_OUT)

            return g.ndata.pop(GNN_NODE_FEAT_OUT)

        else:
            # @TODO: add support for LSTM aggregation for dense graphs 
            # concat
            if self.readout_op == "concat":
                h_concat = [h.squeeze() for h in h_concat]
                h = torch.cat(h_concat, dim=-1)
            # readout
            if with_readout:
                return REDUCE_TYPES[self.readout_type](h, dim=0)
            return h

    def set_rlp(self, with_rlp):
        for layer in self.layers:
            layer.set_rlp(with_rlp)

    def rlp(self, relevance_score):
        for layer_id in range(len(self.layers)-1, -1, -1):
            relevance_score = self.layers[layer_id].rlp(relevance_score)
        return relevance_score 

