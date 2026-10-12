from dissector.pattern_matcher import classify_archetypes


def test_interactive_binary_search_outranks_incidental_letter_mentions():
    text = (
        "The interactor chooses X. Your queries ask whether X is at most Y. "
        "During Interaction, output the answer and flush the output."
    )
    assert classify_archetypes(text)[0].archetype_id == "10"


def test_prime_factor_query_protocol_is_classified_as_interactive():
    text = (
        "Guess N by asking the interactor how many times a prime P occurs "
        "in the prime factorization of N. During Interaction, ask at most "
        "five queries, then print the answer."
    )
    assert classify_archetypes(text)[0].archetype_id == "10"


def test_grid_shortest_distance_is_classified_as_graph_problem():
    text = (
        "Given a matrix of cells, compute the shortest distance from every "
        "empty cell to any special cell. Adjacent cells share a side and "
        "there is a path from every empty cell to a special cell."
    )
    assert classify_archetypes(text)[0].archetype_id == "02"


def test_dictionary_pagination_is_not_overranked_as_string_matching():
    text = (
        "Words appear in lexicographical order in a dictionary. Answer queries: "
        "on what page will word W appear when each page contains X words?"
    )
    assert classify_archetypes(text)[0].archetype_id == "04"


def test_manhattan_distance_is_not_overranked_by_input_string_format():
    text = (
        "Coordinates start at (0, 0). Find the Manhattan distance after moves "
        "in four cardinal directions. Input is a string of N, E, S and W."
    )
    assert classify_archetypes(text)[0].archetype_id == "07"


def test_maximize_profit_phrase_is_not_confused_with_arithmetic_sum():
    text = (
        "Maximize Profit: choose deal order to maximize the final value; "
        "each deal adds a constant or increases the current amount by a percentage."
    )
    assert classify_archetypes(text)[0].archetype_id == "01"


def test_generic_story_use_of_game_does_not_force_game_theory():
    text = (
        "You are playing a game with attack and speed values. Spend all dollars "
        "to bring both values to the same level."
    )
    matches = classify_archetypes(text)
    assert not matches or matches[0].archetype_id != "09"
