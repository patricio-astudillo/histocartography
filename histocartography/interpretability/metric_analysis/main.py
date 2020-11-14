def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

import argparse
from config import *
from explainability import *
from concept_metrics import ConceptMetric, ConceptRanking
from sklearn.metrics import auc
from plotting import *
from histocartography.utils.io import write_json


# ALL_CONCEPTS = ['roundness', 'ellipticity', 'crowdedness', 'std_h', 'area', ]
ALL_CONCEPTS = [
    'area',               #
    'perimeter',          #
    'roughness',          #
    'eccentricity',       #
    'roundness',          #
    'shape_factor',       #
    'crowdedness',        #
    'std_crowdedness',    #
    'glcm_dissimilarity', #   
    'std_h',              # @TODO: is it the same as contrast?
    'glcm_homogeneity',   #
    'glcm_ASM',           #
    'glcm_entropy',       #
    'glcm_variance'       #
]

parser = argparse.ArgumentParser()
parser.add_argument('--explainer',
                    help='Explainability method',
                    choices=['GraphLRP', 'GraphGradCAM', 'GNNExplainer', 'GraphGradCAMpp', '-1'],
                    required=True)
parser.add_argument('--base-path',
                    help='Base path to the data folder',
                    required=False)
parser.add_argument('--classification-mode',
                    help='Classification mode',
                    choices=[2, 3],
                    default=3,
                    type=int,
                    required=False)
parser.add_argument('--extract_features',
                    help='If we should extract nuclei features',
                    default='False',
                    required=False)
# parser.add_argument('--concept',
#                     help='Node concept to analyze', required=True)
parser.add_argument('--p',
                    help='Node importance > p to keep',
                    type=float,
                    default=-1,
                    required=False)
parser.add_argument('--distance',
                    help='Point cloud distance measure',
                    choices=['pair', 'chamfer', 'hausdorff', 'svm', 'hist', 'wassertein'],
                    default='hist',
                    required=False)
parser.add_argument('--nuclei-selection-type',
                    help='Nuclei selection type, eg. w/ hard thresholding, w/ cumulutative',
                    choices=['cumul', 'thresh', 'absolute', 'random'],
                    default='thresh',
                    required=False)
parser.add_argument('--rm-non-epithelial-nuclei',
                    help='If we should remove all the non epithelial nuclei.',
                    default='False',
                    required=False)
parser.add_argument('--risk',
                    help='With class-shift risk',
                    default='True',
                    required=False)
parser.add_argument('--rm-misclassification',
                    help='If we should filter out misclassified samples.',
                    default='True',
                    required=False)
parser.add_argument('--with-nuclei-selection-plot',
                    help='If we should plot the nuclei selection along with the image for each sample.',
                    default='False',
                    required=False)
parser.add_argument('--verbose',
                    help='Verbose flag',
                    default='False',
                    required=False)
parser.add_argument('--visualize',
                    help='Visualize flag',
                    default='False',
                    required=False)


args = parser.parse_args()
config = Configuration(args=args)
# args.concept = args.concept.split(',')

# *************************************************************************** Set parameters
verbose = eval(args.verbose)
visualize = eval(args.visualize)
args.rm_misclassification = eval(args.rm_misclassification)
args.rm_non_epithelial_nuclei = eval(args.rm_non_epithelial_nuclei)
args.with_nuclei_selection_plot = eval(args.with_nuclei_selection_plot)
percentages = config.percentages
explainers = config.explainers

# Get TRoI sample names
config.get_sample_names(args, explainers)
print('Total #TRoI: ', len(config.samples))

# *************************************************************************** Extract features
if eval(args.extract_features):
    from extract_features import *
    extract = ExtractFeatures(config)
    extract.extract_feature()
    exit()

# *************************************************************************** Get explanation
p_concept_scores = []
p_nuclei_scores = []

for e in explainers:
    print('\n********************************************')
    print('Explainer: ', e)
    score_per_concept_per_percentage_per_pair = {}
    stats_per_concept_per_percentage_per_tumor_type = {}

    for concept in ALL_CONCEPTS:
        score_per_concept_per_percentage_per_pair[concept] = {}
        stats_per_concept_per_percentage_per_tumor_type[concept] = {}
        for p in percentages:
            exp = Explainability(
                args=args,
                config=config,
                explainer=e,
                concept_name=concept,
                percentage=p,
                verbose=verbose,
                visualize=visualize
            )
            exp.get_explanation()

            # plot nuclei selection on the original image 
            if args.with_nuclei_selection_plot:
                plot_nuclei_selection(exp, base_path=args.base_path)

            m = ConceptMetric(args=args, config=config, explainer=e, percentage=p, explanation=exp)
            if concept == 'type':
                concept_score_per_pair = m.compute_nuclei_score()
                concept_stats_per_tumor_type = {}
            else:
                concept_stats_per_tumor_type = m.compute_tumor_type_stats()
                concept_score_per_pair = m.compute_concept_score()
            score_per_concept_per_percentage_per_pair[concept][str(p)] = concept_score_per_pair
            stats_per_concept_per_percentage_per_tumor_type[concept][str(p)] = concept_stats_per_tumor_type

            print(
                'Concept= ',
                concept,
                'p= ',
                round(p, 2),
                ' --nTRoI: ',
                np.sum(exp.samples),
                ' --nNodes: ',
                len(exp.labels),
                ' --concept-score= ',
                concept_score_per_pair,
                # ' --stats-tumor-type= ',
                # concept_stats_per_tumor_type
                )

            if visualize:
                #plot_concept_map_per_tumor_type(args, config, e, p, exp)
                plot_concept_map_per_tumor_class(args, config, e, p, exp)
        
        # compute AUC over the values of p for a given concept and for each pair of classes 
        all_pairs = [pair for pair, _ in concept_score_per_pair.items()]
        score_per_concept_per_percentage_per_pair[concept]['auc'] = {}
        for pair in all_pairs:  # loop over all the pairs
            auc_score = auc(percentages,
                            [score_per_concept_per_percentage_per_pair[concept][str(p)][pair] for p in percentages])
            score_per_concept_per_percentage_per_pair[concept]['auc'][pair] = auc_score

        # compute average over the values of p for a given concept and for each tumor type 
        all_tumor_types = [t for t, _ in concept_stats_per_tumor_type.items()]
        stats_per_concept_per_percentage_per_tumor_type[concept]['avg'] = {}
        for t in all_tumor_types:  # loop over all the tumor types
            avg_mean = sum([stats_per_concept_per_percentage_per_tumor_type[concept][str(p)][t]['mean'] for p in percentages]) / len(percentages)
            avg_std = sum([stats_per_concept_per_percentage_per_tumor_type[concept][str(p)][t]['std'] for p in percentages]) / len(percentages)
            avg_ratio = sum([stats_per_concept_per_percentage_per_tumor_type[concept][str(p)][t]['ratio'] for p in percentages]) / len(percentages)
            stats_per_concept_per_percentage_per_tumor_type[concept]['avg'][t] = {
                'mean': float(np.round(avg_mean, 4)),
                'std': float(np.round(avg_std, 4)),
                'ratio': float(np.round(avg_ratio, 4))
            }

    # print & save the scores 
    # for concept_id, (concept_name, concept_val) in enumerate(score_per_concept_per_percentage_per_pair.items()):
    #     print('*** - Concept: {} | ({}/{})'.format(concept_name, concept_id + 1, len(ALL_CONCEPTS)))
    #     for p_id, (p_name, p_val) in enumerate(concept_val.items()):
    #         print('    *** - Percentage: {} | ({}/{})'.format(p_name, p_id + 1, len(percentages)))
    #         for _, (pair_name, pair_val) in enumerate(p_val.items()):
    #             print('        - Class pair: {} with distance: {}'.format(pair_name, pair_val))
    #     print('\n\n')

    for concept_id, (concept_name, concept_val) in enumerate(score_per_concept_per_percentage_per_pair.items()):
        # print('*** - Concept: {} | ({}/{})'.format(concept_name, concept_id + 1, len(ALL_CONCEPTS)))
        # print('    *** - Percentage: {} | ({}/{})'.format(p_name, p_id + 1, len(percentages)))
        out = [np.round(pair_val[1], 4) for _, pair_val in enumerate(concept_val['auc'].items())]
        print(out[0], out[1], out[2])
        # for _, (pair_name, pair_val) in enumerate(p_val.items()):
        #     print('        - Class pair: {} with distance: {}'.format(pair_name, pair_val))

    write_json(e + '_output_pair.json', score_per_concept_per_percentage_per_pair)
    write_json(e + '_output_tumor_stats.json', stats_per_concept_per_percentage_per_tumor_type)

    # # rank the concepts and checking aggreement with pathologists
    # concept_ranker = ConceptRanking(score_per_concept_per_percentage_per_pair)
    # ranking_score_per_pair, aggregated_ranking_score = concept_ranker.rank_concepts(p_to_keep='auc')

# if visualize:
#     plot_auc_map(args, config, p_concept_scores, title='Concept score vs Percentage: ' + args.concept, filename='concept')
#     plot_auc_map(args, config, p_nuclei_scores, title='Nuclei score vs Percentage: ' + args.concept, filename='nuclei')
