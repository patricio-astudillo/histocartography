"""Unit test for preprocessing.feature_extraction"""
import unittest
import numpy as np
import yaml
import os 
import torch 
import shutil

from histocartography import PipelineRunner

class FeatureExtractionTestCase(unittest.TestCase):
    """FeatureExtractionTestCase class."""

    @classmethod
    def setUpClass(self):
        self.current_path = os.path.dirname(__file__)
        self.data_path = os.path.join(self.current_path, '..', 'data')
        self.image_path = os.path.join(self.data_path, 'images')
        self.image_name = '283_dcis_4.png'
        self.out_path = os.path.join(self.data_path, 'feature_extraction_test')
        if os.path.exists(self.out_path) and os.path.isdir(self.out_path):
            shutil.rmtree(self.out_path) 
        os.makedirs(self.out_path)

    def test_handcrafted_feature_extractor(self):
        """
        Test handcrafted feature extractor with pipeline runner.
        """
        config_fname = os.path.join(self.current_path,
                                    'config',
                                    'feature_extraction',
                                    'handcrafted_feature_extractor.yml')
        with open(config_fname, 'r') as file:
            config = yaml.load(file)

        pipeline = PipelineRunner(output_path=self.out_path, save=True, **config)
        pipeline.precompute()
        output = pipeline.run(
            name=self.image_name.replace('.png', ''),
            image_path=os.path.join(self.image_path, self.image_name)
        )
        features = output['features']

        self.assertTrue(isinstance(features, torch.Tensor))  # check type
        self.assertEqual(features.shape[1], 65)  # check number of features per instance
        self.assertEqual(features.shape[0], 22)  # check number of instances detected

        # Re-run with existing output & ensure equal
        output = pipeline.run(
            name=self.image_name.replace('.png', ''),
            image_path=os.path.join(self.image_path, self.image_name)
        )
        reload_features = output['features']

        self.assertTrue(np.array_equal(features, reload_features))

    def test_deep_tissue_feature_extractor_noaug(self):
        """
        Test deep tissue feature extractor with pipeline runner and without augmentation.
        """
        config_fname = os.path.join(self.current_path,
                                    'config',
                                    'feature_extraction',
                                    'deep_tissue_feature_extractor_noaug.yml')
        with open(config_fname, 'r') as file:
            config = yaml.load(file)

        pipeline = PipelineRunner(output_path=self.out_path, save=True, **config)
        pipeline.precompute()
        output = pipeline.run(
            name=self.image_name.replace('.png', ''),
            image_path=os.path.join(self.image_path, self.image_name)
        )
        features = output['features']

        self.assertTrue(isinstance(features, torch.Tensor))  # check type
        self.assertEqual(features.shape[0], 22)    # check number of superpixels
        self.assertEqual(features.shape[1], 1280)  # check number features

        # Re-run with existing output & ensure equal
        output = pipeline.run(
            name=self.image_name.replace('.png', ''),
            image_path=os.path.join(self.image_path, self.image_name)
        )
        reload_features = output['features']

        self.assertTrue(np.array_equal(features, reload_features))

    def test_deep_tissue_feature_extractor_aug(self):
        """
        Test deep tissue feature extractor with pipeline runner and with augmentation.
        """
        config_fname = os.path.join(self.current_path,
                                    'config',
                                    'feature_extraction',
                                    'deep_tissue_feature_extractor_aug.yml')
        with open(config_fname, 'r') as file:
            config = yaml.load(file)

        pipeline = PipelineRunner(output_path=self.out_path, save=True, **config)
        pipeline.precompute()
        output = pipeline.run(
            name=self.image_name.replace('.png', ''),
            image_path=os.path.join(self.image_path, self.image_name)
        )
        features = output['features']

        self.assertTrue(isinstance(features, torch.Tensor))  # check type
        self.assertEqual(features.shape[0], 22)    # check number of superpixels
        self.assertEqual(features.shape[1], 4)     # check number of augmentations
        self.assertEqual(features.shape[2], 1280)  # check number features

        # Re-run with existing output & ensure equal
        output = pipeline.run(
            name=self.image_name.replace('.png', ''),
            image_path=os.path.join(self.image_path, self.image_name)
        )
        reload_features = output['features']

        self.assertTrue(np.array_equal(features, reload_features))

    def test_deep_nuclei_feature_extractor_noaug(self):
        """Test deep instance feature extractor with pipeline runner."""

        config_fname = os.path.join(self.current_path,
                                    'config',
                                    'feature_extraction',
                                    'deep_nuclei_feature_extractor_noaug.yml')
        with open(config_fname, 'r') as file:
            config = yaml.load(file)

        pipeline = PipelineRunner(output_path=self.out_path, save=True, **config)
        pipeline.precompute()
        output = pipeline.run(
            name=self.image_name.replace('.png', ''),
            image_path=os.path.join(self.image_path, self.image_name)
        )
        features = output['features']

        self.assertTrue(isinstance(features, torch.Tensor))  # check type
        self.assertEqual(features.shape[0], 331)             # check number of nuclei
        self.assertEqual(features.shape[1], 1280)            # check number features

    def test_deep_nuclei_feature_extractor_aug(self):
        """Test deep instance feature extractor with pipeline runner."""

        config_fname = os.path.join(self.current_path,
                                    'config',
                                    'feature_extraction',
                                    'deep_nuclei_feature_extractor_aug.yml')
        with open(config_fname, 'r') as file:
            config = yaml.load(file)

        pipeline = PipelineRunner(output_path=self.out_path, save=True, **config)
        pipeline.precompute()
        output = pipeline.run(
            name=self.image_name.replace('.png', ''),
            image_path=os.path.join(self.image_path, self.image_name)
        )
        features = output['features']

        self.assertTrue(isinstance(features, torch.Tensor))  # check type
        self.assertEqual(features.shape[0], 331)   # check number of nuclei
        self.assertEqual(features.shape[1], 4)     # check number of augmentations
        self.assertEqual(features.shape[2], 1280)  # check number features


    def tearDown(self):
        """Tear down the tests."""


if __name__ == "__main__":

    unittest.main()
