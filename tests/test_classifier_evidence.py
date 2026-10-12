from dissector.pattern_matcher import classify_archetypes


def test_game_evidence_outranks_generic_optimization_words():
    text = "A game where players take turns and both play optimally; maximize or minimize the score."
    matches = classify_archetypes(text)
    assert matches[0].archetype_id == "09"
