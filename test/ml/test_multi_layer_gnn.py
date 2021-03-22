"""Unit test for ml.layers.multi_layer_gnn"""
import unittest
import torch
import dgl  
import yaml
import os 

from histocartography.ml.layers.multi_layer_gnn import MultiLayerGNN

BASE_S3 = 's3://mlflow/'
IS_CUDA = torch.cuda.is_available()


class MultiLayerGNNTestCase(unittest.TestCase):
    """MultiLayerGNN class."""

    @classmethod
    def setUpClass(self):
        self.current_path = os.path.dirname(__file__)

    def test_multi_layer_gnn(self):
        """
        Test MultiLayerGNN. 
        """

        # 1. load dummy config
        config_fname = os.path.join(self.current_path, 'config', 'multi_layer_gnn.yml')
        with open(config_fname, 'r') as file:
            config = yaml.load(file)['model']

        # 2. dummy data
        graph = dgl.rand_graph(100, 10)
        features = torch.rand(100, 512)

        # 2. multi layer GNN
        model = MultiLayerGNN(input_dim=512, **config)
        out = model(graph, features, with_readout=False)
    
        # 3. tests 
        self.assertIsInstance(out, torch.Tensor)
        self.assertEqual(out.shape[0], 100)
        self.assertEqual(out.shape[1], 96)  # 3 layers x 32 hidden dimension

    def tearDown(self):
        """Tear down the tests."""


if __name__ == "__main__":
    unittest.main()