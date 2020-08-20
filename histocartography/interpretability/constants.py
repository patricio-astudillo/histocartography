# define all the available modules for interpretability 
AVAILABLE_EXPLAINABILITY_METHODS = {
    'pruning_explainer.graph_pruning_explainer': 'GraphPruningExplainer',
    'lrp_explainer.lrp_gnn_explainer': 'LRPGNNExplainer',
    'attention_based_explainer.attention_gnn_explainer': 'AttentionGNNExplainer',
}


BASE_S3 = 's3://mlflow/'


# Assuming the class split is thr 5-class scenario one 
MODEL_TO_MLFLOW_ID = {
    'attention_based_explainer.attention_gnn_explainer': BASE_S3 + '70a419364cda43548a6e3733ad0ef0b5/artifacts/model_best_val_weighted_f1_score_0',
    'pruning_explainer.graph_pruning_explainer': BASE_S3 + '55ebbd5a765e4a1d80818112212e1875/artifacts/model_best_val_loss_0',
    'lrp_explainer.lrp_gnn_explainer': BASE_S3 + '7ad2792ad69940e0a54dc554af3c4716/artifacts/model_best_val_weighted_f1_score_0',
    'saliency_explainer.graph_cam': BASE_S3 + ''
}


INTERPRETABILITY_MODEL_TYPE_TO_LOAD_FN = {
    'attention_based_explainer.attention_gnn_explainer': 'plain_model_loading',
    'pruning_explainer.graph_pruning_explainer': 'tentative_model_loading',
    'lrp_explainer.lrp_gnn_explainer': 'plain_model_loading',
    'saliency_explainer.graph_cam': 'plain_model_loading'
}


EXPLANATION_TYPE_SAVE_SUBDIR = {
    'attention_based_explainer.attention_gnn_explainer': 'GAT',
    'pruning_explainer.graph_pruning_explainer': 'GNNExplainer',
    'lrp_explainer.lrp_gnn_explainer': 'GraphLRP'
}