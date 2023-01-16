# Scior-Tester: Build Function

## Contents

- [Description](#description)
- [Input Catalog Datasets](#input-catalog-datasets)
  - [Input Models Selection](#input-models-selection)
  - [Exceptional Cases](#exceptional-cases)
- [Creation of Directories and Files](#creation-of-directories-and-files)
  - [Taxonomical Graphs Separation Procedure](#taxonomical-graphs-separation-procedure)
  - [OntoUML Stereotype and gUFO Classification](#ontouml-stereotype-and-gufo-classification)
- [Execution Instructions](#execution-instructions)
  - [OntoUML/UFO Catalog](#ontoumlufo-catalog)
  - [Scior-Tester’s Build Execution](#scior-testers-build-execution)

## Description

As the Scior-Tester build function creates the structure necessary for performing the tests, its execution is mandatory before the execution of the tests. Once executed, the build function reads the information from the [OntoUML/UFO Catalog](https://github.com/unibz-core/ontouml-models) and creates a new directory structure for each of its datasets that are eligible for receiving the tests. In this documentation, we present all the points necessary for understanding and performing the build function, as well as its generated results.

## Input Catalog Datasets

The build function reads data from the [OntoUML/UFO Catalog](https://github.com/unibz-core/ontouml-models) for creating the internal structure necessary for performing the Scior tests. In the current implementation, the Scior-Tester reads the data from the user's filesystem (i.e., offline), hence, the catalog must be available as a folder.

### Input Models Selection

However, not all datasets that are part of the catalog are eligible for receiving the tests. Their selection criteria are:

1. The dataset's ontology model must comply exclusively with the OntoUML syntax (i.e., datasets with models formalized directly specializing UFO concepts or that use both OntoUML and UFO are excluded)
1. The dataset's OntoUML model must contain at least one taxonomy (i.e., models with no generalization/specialization relations are not eligible for the tests)

A list called `EXCEPTIONS_LIST`, available in the project's `__init__.py` [file](https://github.com/unibz-core/Scior/blob/main/scior/__init__.py), registers the excluded datasets (i.e., the datasets that will not be processed by the Tester). By downloading the Scior-Tester, this list is already going to be filled in, however the user can manipulate this list in case of need.

### Exceptional Cases

When trying to extract the taxonomy from the dataset *van-ee2021modular*, the tester reports a stack overflow error. Hence, this repository was included into the `EXCEPTIONS_LIST`. A more precise evaluation of the problem needs to be done to understand and solve this issue (see [open issue #12](https://github.com/unibz-core/Scior-Tester/issues/12)).

## Creation of Directories and Files

The build function receives as argument the path to the folder containing the OntoUML/UFO Catalog content. Once executed, the build function creates a similar folder structure inside the Tester's project folder:

```txt
/catalog/
    +---dataset1/
    |   dataset1_tx001.ttl
    |   dataset1_tx002.ttl
    |   data_dataset1_tx001.csv
    |   data_dataset1_tx002.csv
    +---dataset2/
    +---dataset3/
    ...
    +---datasetN/
    +---taxonomies.csv
    +---hash_sha256_register.csv
```

As can be seen in the representation above, the only file generated outside the datasets folders is the `hash_sha256_register.csv`, which is used for tracking purposes—[access this link](https://github.com/unibz-core/Scior-Dataset#hashes-register-csv-file) for more information about it. We describe the generation of each file inside the datasets folders in the next section. Finally, the description of the internal content of each file generated by the build function is described in the Scior-Dataset's documentation, which [can be accessed in this link](https://github.com/unibz-core/Scior-Dataset#build-generated-files).

### Taxonomical Graphs Separation Procedure

The main procedure performed by the build function is the *taxonomical graphs separation*, where an input ontology graph (where each owl:Class is a graph node) has its* individual taxonomies separated in different graphs, generating the [taxonomical graph *ttl* files](https://github.com/unibz-core/Scior-Dataset#taxonomical-graph-ttl-file) and the [taxonomical graph information *csv* files](https://github.com/unibz-core/Scior-Dataset#taxonomical-graph-information-csv-file).

The procedure's algorithm is the following:

1. All object properties' that differ from `rdfs:subClassOf` or `rdf:type` are removed from the original graph
2. All ontology classes with no taxonomical relation are discarded (i.e., every `owl:Class` without an `rdfs:subClassOf` relation to other `owl:Class`)
3. A list of root nodes is generated and, for its first element, all other nodes that are reachable from it (i.e., nodes that can be accessed via the specialization/generalization relations) are separated into a new taxonomical graph and their information is separated in a new file
4. The root node selected as a pivot is removed from the root list. If any of its reachable nodes are also at the root list, it is also removed from there
5. Step 3 is performed again with the new root list up to when the root list is empty

We present in the image below an example of how the taxonomy separation procedure works.

<img src="https://user-images.githubusercontent.com/8641647/207654250-3434e2b7-036c-43b6-94a5-66f95f5d41bc.png" width="600">

By applying the algorithm presented in the original graph of figure above, we have as results two taxonomies. Note that classes C08, C09, and C10 were discarded during the algorithm's step 2. The algorithm's step 3 generates the following list of root nodes: C01, C02, C03, and C11. Using C01 as a pivot, all its reachable nodes (algorithm's step 4) are: C04 and C05. Hence, these classes are separated into a new graph and the root list is updated without C01 and their related nodes. The new list is C02, C03, and C11. A second taxonomy is generated with all remaining classes as, by applying the same algorithm, all remaining classes are reachable from C02. By the end of the process, there are no mode root nodes and the algorithm ends.

In the image, the different colors represent the different gUFO classifications associated to the graph's classes. By The resulting taxonomies do not have any associated gUFO information, and only taxonomical relations are kept.

In the example represented in the figure, four files are going to be generated inside the corresponding dataset folder:

- catalog/dataset-name/dataset-name_tx001.ttl
- catalog/dataset-name/dataset-name_tx002.ttl
- catalog/dataset-name/data_dataset-name_tx001.csv
- catalog/dataset-name/data_dataset-name_tx002.csv

Access the following links for consulting the documentation of the internal structure of the [taxonomical graph *ttl* files](https://github.com/unibz-core/Scior-Dataset#taxonomical-graph-ttl-file) and the [taxonomical graph information *csv* files](https://github.com/unibz-core/Scior-Dataset#taxonomical-graph-information-csv-file).

### OntoUML Stereotype and gUFO Classification

The aim of Scior is to infer the gUFO endurant types of OWL classes. For achieving its goal, it uses gUFO—and not OntoUML—information provided as input. As the tests use OntoUML models from the OntoUML/UFO Catalog, a mapping between the OntoUML stereotypes and the gUFO endurant types is necessary.

Limiting the mapping scope to gUFO endurant types, the characteristics that must be observed from the OntoUML stereotypes are only their [sortality](https://ontouml.readthedocs.io/en/latest/theory/identity.html) and [rigidity](https://ontouml.readthedocs.io/en/latest/theory/rigidity.html). The other characteristic that the stereotypes have can be called "*ontological nature*". However, this last characteristic is related to the gUFO individuals' hierarchy and is, for this Scior version, out of scope.

All stereotypes and classification names were set to lower case and spaces were removed for the correct mapping. The mapping occurs as follows:

1. Classes with the following OntoUML stereotypes receive a gUFO classification with the same name of the stereotype: `category`, `mixin`, `phase`, `phasemixin`, `kind`, `subkind`, `role`, `rolemixin`.
2. Classes with OntoUML stereotypes `collective`, `quality`, `quantity`, `mode`, or `relator` are mapped to the gUFO classification `kind`.
3. The stereotype `historicalrole` is mapped to the gUFO classification `role`, and `historicalrolemixin` is mapped to `rolemixin`.
4. Finally, classes without OntoUML stereotypes or with stereotypes not cited here receive the string "other" as gUFO classification.

The information of the OntoUML stereotype and the corresponding gUFO classification for each class are preserved in the information *csv* file for the Scior tests to be executed and for having their results evaluated.

## Execution Instructions

### OntoUML/UFO Catalog

The OntoUML/UFO Catalog must be available as a folder in the user's filesystem, so it can be used by the Scior-Tester's build function. For that, you must clone its GitHub repository—you can find precise instructions about how to do that [in this link](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

### Scior-Tester’s Build Execution

For running the Scior-Tester's build function, you must execute the following command from the project folder at your terminal:

```shell
python ./src/scior_tester.py -b path-to-catalog
```

Note: the instructions here provided may not work properly in the Tester's current implementation—please refer to [issue #14](https://github.com/unibz-core/Scior-Tester/issues/14).