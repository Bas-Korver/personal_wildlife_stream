from difflib import SequenceMatcher

import requests


def get_animal_data(animal_name: str) -> str:
    animal = {
        "common_name": animal_name,
        "scientific_name": "",
        "hierarchy": {},
        "subspecies": [],
    }

    # Get animal data from ITIS web service based on the common name.
    animal_data = requests.get(
        f"https://www.itis.gov/ITISWebService/jsonservice/getITISTermsFromCommonName?srchKey={animal_name}"
    ).json()
    animal_data = [
        item for item in animal_data["itisTerms"] if item["commonNames"][0] is not None
    ]

    # Get similarity ratios between the provided common name and each common name in the API data.
    similarity_ratios = [
        [
            SequenceMatcher(None, animal_name.lower(), common_name.lower()).ratio()
            for common_name in item["commonNames"]
        ]
        for item in animal_data
    ]

    # Find index of highest similarity ratio.
    max_index = max(
        ((i, j) for i, row in enumerate(similarity_ratios) for j, _ in enumerate(row)),
        key=lambda index: similarity_ratios[index[0]][index[1]],
    )

    # Get the scientific name of max index.
    animal["scientific_name"] = animal_data[max_index[0]]["scientificName"]

    # Get taxonomic hierarchy of animal.
    animal_taxonomic_hierarchy_data = requests.get(
        f"http://www.itis.gov/ITISWebService/jsonservice/getFullHierarchyFromTSN?tsn={animal_data[max_index[0]]['tsn']}"
    ).json()["hierarchyList"]

    seen_ranks = []
    duplicate_ranks = {}

    # Identify duplicate ranks
    for item in animal_taxonomic_hierarchy_data:
        if item["rankName"] not in seen_ranks:
            seen_ranks.append(item["rankName"])
        else:
            duplicate_ranks[item["rankName"]] = 0

    # Initialize the animal hierarchy structure
    animal["hierarchy"] = {rank: [] for rank in duplicate_ranks}

    # Populate the animal hierarchy
    for item in animal_taxonomic_hierarchy_data:
        if item["rankName"] in duplicate_ranks:
            animal["hierarchy"][item["rankName"]].append(item["taxonName"])
        else:
            animal["hierarchy"][item["rankName"]] = item["taxonName"]

    # Get subspecies of animal.
    animal["subspecies"] = [
        subspecies["taxonName"]
        for subspecies in requests.get(
            f"http://www.itis.gov/ITISWebService/jsonservice/getHierarchyDownFromTSN?tsn={animal_data[max_index[0]]['tsn']}"
        ).json()["hierarchyList"]
    ]

    return animal
