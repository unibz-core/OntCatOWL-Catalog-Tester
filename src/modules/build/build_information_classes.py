""" Functions related to the statistics building, collection and saving. """
import csv

from src import CLASSES_DATA_FILE_NAME, NAMESPACE_TAXONOMY
from src.modules.tester.hash_functions import register_sha256_hash_information
from src.modules.tester.logger_config import initialize_logger
from src.modules.tester.utils_graph import get_all_superclasses, get_all_subclasses, get_all_related_nodes


class InformationStructure(object):
    """ Used for storing information about a class in a dataset. """

    def __init__(self, name, stereotype_original=None, stereotype_gufo=None, is_root=None, is_leaf=None,
                 is_intermediate=None, number_superclasses=None, number_subclasses=None,
                 number_reachable_classes=None):
        # General attributes
        self.name: str = name
        self.prefixed_name: str = NAMESPACE_TAXONOMY + name

        # Stereotypes attributes
        self.stereotype_original: str = stereotype_original
        self.stereotype_gufo: str = stereotype_gufo

        # Taxonomy position attributes
        self.is_root: bool = is_root
        self.is_leaf: bool = is_leaf
        self.is_intermediate: bool = is_intermediate

        # Taxonomy relations attributes
        self.number_superclasses: int = number_superclasses
        self.number_subclasses: int = number_subclasses
        self.number_reachable_classes: int = number_reachable_classes

    def convert_to_row(self) -> list:
        return [self.name, self.stereotype_original, self.stereotype_gufo, self.is_root, self.is_leaf,
                self.is_intermediate, self.number_superclasses, self.number_subclasses, self.number_reachable_classes]

    def build_position(self, taxonomy_nodes):
        self.is_root = self.prefixed_name in taxonomy_nodes["roots"]
        self.is_leaf = self.prefixed_name in taxonomy_nodes["leaves"]
        self.is_intermediate = (not self.is_root) and (not self.is_leaf)

    def build_numbers(self, taxonomy_nodes, taxonomy_graph):
        self.number_superclasses = len(get_all_superclasses(taxonomy_graph, taxonomy_nodes, self.prefixed_name))
        self.number_subclasses = len(get_all_subclasses(taxonomy_graph, taxonomy_nodes, self.prefixed_name))
        self.number_reachable_classes = len(get_all_related_nodes(taxonomy_graph, taxonomy_nodes, self.prefixed_name))


def saves_dataset_csv_classes_data(catalog_information, dataset_path, catalog_size, current,
                                   source_owl_file_path, hash_register):
    """ Saves dataset classes information in CSV format. """

    logger = initialize_logger()
    csv_header = ["class_name", "stereotype_original", "stereotype_gufo", "is_root", "is_leaf", "is_intermediate",
                  "number_superclasses", "number_subclasses", "number_reachable_classes"]

    csv_file_full_path = dataset_path + "\\" + CLASSES_DATA_FILE_NAME

    with open(csv_file_full_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)

        for class_information in catalog_information:
            writer.writerow(class_information.convert_to_row())

    logger.info(f"CSV file {current}/{catalog_size} saved: {csv_file_full_path}\n")

    hash_register = register_sha256_hash_information(hash_register, csv_file_full_path, source_owl_file_path)

    return csv_file_full_path, hash_register
