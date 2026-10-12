from dissector.pattern_matcher import classify_archetypes


def test_matrix_rotation_is_recognized_as_geometry():
    matches = classify_archetypes(
        "Matrix Rotations: rotate a square matrix by 90 degrees and combine "
        "the original and rotated matrices."
    )
    assert matches[0].archetype_id == "07"


def test_simple_addition_has_arithmetic_evidence():
    matches = classify_archetypes(
        "You are given two integer values A and B; compute and output their sum."
    )
    assert matches[0].archetype_id == "05"


def test_word_choice_is_not_misranked_by_lexicographic_phrase_alone():
    matches = classify_archetypes(
        "Given a list of words, keep one letter from each word and build the "
        "lexicographically smallest word."
    )
    assert matches[0].archetype_id == "08"


def test_constructive_flip_prefix_signal_outranks_string_prefix_signal():
    matches = classify_archetypes(
        "Flip the prefix of a sequence to obtain the required construction."
    )
    assert matches[0].archetype_id == "10"


def test_shortest_routes_and_four_direction_movement_signal_graphs():
    matches = classify_archetypes(
        "Walk in four directions: up, down, left or right. Count cells "
        "equally close by shortest routes to two destinations."
    )
    assert matches[0].archetype_id == "02"


def test_tree_evidence_outranks_generic_edge_mentions():
    matches = classify_archetypes(
        "You are given a tree with N nodes. Find the minimum number of edges to cut."
    )
    assert matches[0].archetype_id == "03"


def test_bottle_minimization_is_recognized_as_greedy_evidence():
    matches = classify_archetypes(
        "What is the minimum number of bottles needed to fill at least K glasses?"
    )
    assert matches[0].archetype_id == "06"


def test_consecutive_sum_output_form_is_recognized_as_constructive():
    matches = classify_archetypes(
        "Write N as a sum of at least two positive consecutive integers and "
        "output the smallest and largest terms."
    )
    assert matches[0].archetype_id == "10"
