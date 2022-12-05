""" Main module for the OntoCatOWL-Catalog Tester. """
import os
import pandas as pd

from copy import deepcopy
from rdflib import URIRef, RDF

from src import *
from src.modules.build.build_classes_stereotypes_information import collect_stereotypes_classes_information
from src.modules.build.build_directories_structure import get_list_ttl_files, \
    create_test_directory_folders_structure, create_test_results_folder, create_internal_catalog_path
from src.modules.build.build_information_classes import saves_dataset_csv_classes_data
from src.modules.build.build_taxonomy_classes_information import collect_taxonomy_information
from src.modules.build.build_taxonomy_files import create_taxonomy_ttl_file
from ontcatowl import run_ontcatowl
from src.modules.run.test1 import load_baseline_dictionary, remaps_to_gufo, create_classes_yaml_output, \
    create_classes_results_csv_output, create_times_csv_output, create_statistics_csv_output, create_summary_csv_output
from src.modules.tester.hash_functions import write_sha256_hash_register
from src.modules.tester.input_arguments import treat_arguments
from src.modules.tester.logger_config import initialize_logger
from src.modules.tester.utils_rdf import load_graph_safely


def build_ontcatowl_tester(catalog_path):
    """ Build function for the OntoCatOWL-Catalog Tester. Generates all the needed data."""

    # Building directories structure
    datasets = get_list_ttl_files(catalog_path, name="ontology")  # returns all ttl files we have with full path
    catalog_size = len(datasets)
    logger.info(f"The catalog contains {catalog_size} datasets.\n")
    internal_catalog_folder = os.getcwd() + "\\catalog\\"
    create_internal_catalog_path(internal_catalog_folder)
    hash_register = pd.DataFrame(columns=["file_name", "file_hash", "source_file_name", "source_file_hash"])

    for (current, dataset) in enumerate(datasets):
        dataset_name = dataset.split("\\")[-2]
        if dataset_name not in EXCEPTIONS_LIST:
            dataset_folder = internal_catalog_folder + dataset_name
            logger.info(f"### Starting dataset {current}/{catalog_size}: {dataset_name} ###\n")

            create_test_directory_folders_structure(dataset_folder, catalog_size, current)

            # Building taxonomies files and collecting information from classes
            taxonomy_file, hash_register = create_taxonomy_ttl_file(
                dataset, dataset_folder, catalog_size, current, hash_register)

            # Builds dataset_classes_information and collects attributes name, prefixed_name, and all taxonomic information
            dataset_classes_information = collect_taxonomy_information(taxonomy_file, catalog_size, current)

            # Collects stereotype_original and stereotype_gufo for dataset_classes_information
            collect_stereotypes_classes_information(dataset, dataset_classes_information, catalog_size, current)

            _, hash_register = saves_dataset_csv_classes_data(dataset_classes_information, dataset_folder,
                                                              catalog_size, current, dataset, hash_register)

    write_sha256_hash_register(hash_register, internal_catalog_folder + HASH_FILE_NAME)


def run_ontcatowl_test1(catalog_path):
    # Test 1 for OntCatOWL - described in: https://github.com/unibz-core/OntCatOWL-Dataset
    TEST_NUMBER = 1

    list_datasets = get_list_ttl_files(catalog_path, name="taxonomy")
    list_datasets_paths = []
    list_datasets_taxonomies = []

    #global_configurations = {"is_automatic": TEST1_AUTOMATIC,
    #                         "is_complete": TEST1_COMPLETE}

    # Creating list of dataset paths and taxonomies
    total_dataset_number = len(list_datasets)
    for (current, dataset) in enumerate(list_datasets):

        logger.info(f"Executing OntCatOWL for dataset {current}/{total_dataset_number}: {dataset}\n")

        tester_catalog_folder = str(pathlib.Path().resolve()) + r"\catalog"
        dataset_folder = tester_catalog_folder + "\\" + dataset
        list_datasets_paths.append(dataset_folder)
        dataset_taxonomy = dataset_folder + "\\" + "taxonomy.ttl"
        list_datasets_taxonomies.append(dataset_taxonomy)

        input_classes_list = load_baseline_dictionary(dataset)
        input_graph = load_graph_safely(dataset_taxonomy)

        if global_configurations["is_automatic"]:
            l1 = "a"
        else:
            l1 = "i"
        if global_configurations["is_complete"]:
            l2 = "c"
        else:
            l2 = "n"

        test_name = f"test_{TEST_NUMBER}_{l1}{l2}"
        test_results_folder = dataset_folder + "\\" + test_name
        create_test_results_folder(test_results_folder)

        # Executions of the test
        execution_number = 1
        tests_total = len(input_classes_list)

        known_inconsistecies = []
        known_consistencies = []

        for input_class in input_classes_list:
            execution_name = test_name + "_exec" + str(execution_number)

            if (input_class.class_name in known_inconsistecies) or (input_class.class_name in known_consistencies):
                execution_number += 1
                continue

            working_graph = deepcopy(input_graph)
            triple_subject = URIRef(NAMESPACE_TAXONOMY + input_class.class_name)
            triple_predicate = RDF.type
            class_gufo_type = remaps_to_gufo(input_class.class_name, input_class.class_stereotype)
            triple_object = URIRef(class_gufo_type)
            working_graph.add((triple_subject, triple_predicate, triple_object))
            working_graph.bind("gufo", "http://purl.org/nemo/gufo#")

            if execution_number == tests_total:
                end = "\n"
            else:
                end = ""

            try:
                ontology_dataclass_list, time_register, consolidated_statistics = run_ontcatowl(global_configurations,
                                                                                                working_graph)
            except:
                logger.error(f"INCONSISTENCY found! Test {execution_number}/{tests_total} "
                             f"for input class {input_class.class_name} interrupted.{end}")
                create_inconsistency_csv_output(test_results_folder, execution_number, input_class)
            else:
                logger.info(f"Test {execution_number}/{tests_total} "
                            f"for input class {input_class.class_name} successfully executed.{end}")
                # Creating resulting files
                create_classes_yaml_output(input_class, ontology_dataclass_list, test_results_folder, execution_name)
                create_classes_results_csv_output(input_classes_list, ontology_dataclass_list, dataset_folder,
                                                  test_results_folder, execution_name)
                create_times_csv_output(time_register, test_results_folder, execution_number, execution_name)
                create_statistics_csv_output(ontology_dataclass_list, consolidated_statistics, test_results_folder,
                                             execution_number)
                create_summary_csv_output(test_results_folder, execution_number, input_class)

            execution_number += 1


def run_ontcatowl_test2(catalog_path):
    # Test 2 for OntCatOWL - described in: https://github.com/unibz-core/OntCatOWL-Dataset

    list_datasets = get_list_ttl_files(catalog_path)

    global_configurations = {"is_automatic": True,
                             "is_complete": True}

    # Creating list of dataset paths and taxonomies
    current_dataset_number = 1
    total_dataset_number = len(list_datasets)

    for dataset in list_datasets:

        tester_catalog_folder = str(pathlib.Path().resolve()) + r"\catalog"
        dataset_folder = tester_catalog_folder + "\\" + dataset
        list_datasets_paths.append(dataset_folder)
        dataset_taxonomy = dataset_folder + "\\" + "taxonomy.ttl"

        input_classes_list = load_baseline_dictionary(dataset)
        input_graph = load_graph_safely(dataset_taxonomy)

        if global_configurations["is_automatic"]:
            l1 = "a"
        else:
            l1 = "i"
        if global_configurations["is_complete"]:
            l2 = "c"
        else:
            l2 = "n"

        # Executions of the test
        model_size = len(input_classes_list)

        logger.info(f"Executing OntCatOWL for "
                    f"dataset {current_dataset_number}/{total_dataset_number}: {dataset} with {model_size} classes\n")
        current_dataset_number += 1

        # Consider only datasets that have at least 20 classes. If less, skip.
        if model_size < MINIMUM_ALLOWED_NUMBER_CLASSES:
            logger.warning(f"The dataset {dataset} has only {model_size} classes (less than 20) and was skipped.\n")
            continue

        test_name = f"test_{TEST_NUMBER}_{l1}{l2}"
        test_results_folder = dataset_folder + "\\" + test_name
        create_test_results_folder(test_results_folder)

        current_percentage = PERCENTAGE_INITIAL
        while current_percentage <= PERCENTAGE_FINAL:

            current_execution = 1
            number_of_input_classes = round(model_size * current_percentage / 100)

            while current_execution <= NUMBER_OF_EXECUTIONS_PER_DATASET_PER_PERCENTAGE:

                if current_execution == NUMBER_OF_EXECUTIONS_PER_DATASET_PER_PERCENTAGE:
                    end = "\n"
                else:
                    end = ""

                sample_list = random.sample(input_classes_list, number_of_input_classes)

                working_graph = deepcopy(input_graph)
                working_graph.bind("gufo", "http://purl.org/nemo/gufo#")

                for input_class in sample_list:
                    triple_subject = URIRef(NAMESPACE_TAXONOMY + input_class.class_name)
                    triple_predicate = RDF.type
                    class_gufo_type = remaps_to_gufo(input_class.class_name, input_class.class_stereotype)
                    triple_object = URIRef(class_gufo_type)
                    working_graph.add((triple_subject, triple_predicate, triple_object))

                try:
                    ontology_dataclass_list, time_register, consolidated_statistics = run_ontcatowl(
                        global_configurations,
                        working_graph)
                except:
                    logger.error(f"INCONSISTENCY found in: dataset {dataset} - "
                                 f"percentage {current_percentage} - excecution {current_execution}. "
                                 f"Current execution interrupted.{end}")
                    create_inconsistency_csv_output_t2(test_results_folder, current_percentage, current_execution,
                                                       PERCENTAGE_INITIAL)
                else:
                    logger.info(f"Test dataset {dataset} - percentage {current_percentage} - "
                                f"excecution {current_execution} successfully executed "
                                f"({number_of_input_classes} input classes).{end}")
                    # Creating resulting files
                    create_classes_yaml_output_t2(sample_list, ontology_dataclass_list, test_results_folder,
                                                  current_percentage, current_execution, dataset_taxonomy)
                    create_classes_results_csv_output_t2(input_classes_list, ontology_dataclass_list,
                                                         test_results_folder, current_percentage, current_execution,
                                                         dataset_taxonomy)
                    times_file_name = create_times_csv_output_t2(time_register, test_results_folder, current_percentage,
                                                                 current_execution, PERCENTAGE_INITIAL)

                    statistics_file_name = create_statistics_csv_output_t2(ontology_dataclass_list,
                                                                           consolidated_statistics,
                                                                           test_results_folder,
                                                                           current_percentage, current_execution,
                                                                           PERCENTAGE_INITIAL)

                current_execution += 1

            current_percentage += PERCENTAGE_RATE
        register_sha256_hash_information(times_file_name, dataset_taxonomy)
        register_sha256_hash_information(statistics_file_name, dataset_taxonomy)


if __name__ == '__main__':

    logger = initialize_logger()

    arguments = treat_arguments(SOFTWARE_ACRONYM, SOFTWARE_NAME, SOFTWARE_VERSION, SOFTWARE_URL)

    # Execute in BUILD mode.
    if arguments["build"]:
        build_ontcatowl_tester(arguments["catalog_path"])

    # Execute in RUN mode.
    if arguments["run1"]:
        run_ontcatowl_test1(arguments["catalog_path"])

    if arguments["run2"]:
        run_ontcatowl_test2(arguments["catalog_path"])

# TODO (@pedropaulofb): VERIFY
# Are there any classes with more than one stereotype?
# Try to clean garbage classes for creating better statistics
# The following datasets don't have any taxonomy and were removed by hand:
# - chartered-service, experiment2013, gailly2016value, pereira2020ontotrans, zhou2017hazard-ontology-robotic-strolling, zhou2017hazard-ontology-train-control
# van-ee2021modular - RecursionError: maximum recursion depth exceeded while calling a Python object
