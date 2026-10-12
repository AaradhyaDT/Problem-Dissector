from dissector.pattern_matcher import classify_archetypes


def test_shoe_pairing_uses_pair_specific_evidence():
    text = (
        "Any left shoe can be paired with any right shoe of the same size. "
        "Find the maximum number of shoe pairs."
    )
    assert classify_archetypes(text)[0].archetype_id == "06"


def test_divisibility_expression_is_recognized_as_number_theory():
    text = (
        "Count pairs of integers in an array whose sum is divisible by 3."
    )
    assert classify_archetypes(text)[0].archetype_id == "05"


def test_bitwise_query_task_is_recognized_as_data_structure_query_problem():
    text = (
        "You are given Q queries. Count values y in a range such that "
        "x bitwise and y equals x."
    )
    assert classify_archetypes(text)[0].archetype_id == "04"


def test_seven_segment_display_cue_is_detected():
    text = (
        "A seven-segment display uses a number of segments to represent digits. "
        "Find the smallest number using exactly K segments."
    )
    assert classify_archetypes(text)[0].archetype_id == "04"


def test_monotone_subarray_cue_is_ranked_as_dynamic_programming():
    text = "Find the longest monotone subarray of an integer array."
    assert classify_archetypes(text)[0].archetype_id == "01"


def test_nested_segments_cue_is_ranked_as_range_data_structure():
    text = (
        "You are given N segments. Count segments nested inside at least one "
        "other segment."
    )
    assert classify_archetypes(text)[0].archetype_id == "04"
