#!/usr/bin/env python3
"""
instance_generator.py
Generates the ABox (instance layer) for the Texas Hold'em Poker Ontology.
Produces: instances.ttl

Three blocks of test instances:
  Block 1 - Hands WITH explicit hasHandRanking   (coherence test)
  Block 2 - Hands WITHOUT hasHandRanking          (inference test)
  Block 3 - Invalid / edge-case hands             (inconsistency test)
"""

import os

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "instances.ttl")

RANKS = ["Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
         "Nine", "Ten", "Jack", "Queen", "King", "Ace"]
SUITS = ["Spades", "Hearts", "Diamonds", "Clubs"]

HAND_RANKINGS = {
    "RoyalFlush":    "RoyalFlushRanking",
    "StraightFlush": "StraightFlushRanking",
    "FourOfAKind":   "FourOfAKindRanking",
    "FullHouse":     "FullHouseRanking",
    "Flush":         "FlushRanking",
    "Straight":      "StraightRanking",
    "ThreeOfAKind":  "ThreeOfAKindRanking",
    "TwoPair":       "TwoPairRanking",
    "OnePair":       "OnePairRanking",
    "HighCard":      "HighCardRanking",
}

# ══════════════════════════════════════════════════════════════════
# BLOCK 1: Hands with explicit ranking (coherence test)
# The reasoner should confirm these are consistent with Module 13.
# ══════════════════════════════════════════════════════════════════
EXPLICIT_HANDS = [
    # --- Royal Flush (2) ---
    ("Hand_RoyalFlush_Spades",
     "RoyalFlush",
     ["TenOfSpades", "JackOfSpades", "QueenOfSpades", "KingOfSpades", "AceOfSpades"]),

    ("Hand_RoyalFlush_Hearts",
     "RoyalFlush",
     ["TenOfHearts", "JackOfHearts", "QueenOfHearts", "KingOfHearts", "AceOfHearts"]),

    # --- Steel Wheel: A-2-3-4-5 suited (1) ---
    ("Hand_SteelWheel_Diamonds",
     "StraightFlush",
     ["AceOfDiamonds", "TwoOfDiamonds", "ThreeOfDiamonds", "FourOfDiamonds", "FiveOfDiamonds"]),

    # --- Straight Flush standard (2) ---
    ("Hand_StraightFlush_Low_Clubs",
     "StraightFlush",
     ["TwoOfClubs", "ThreeOfClubs", "FourOfClubs", "FiveOfClubs", "SixOfClubs"]),

    ("Hand_StraightFlush_High_Spades",
     "StraightFlush",
     ["EightOfSpades", "NineOfSpades", "TenOfSpades", "JackOfSpades", "QueenOfSpades"]),

    # --- Four of a Kind (2) ---
    ("Hand_FourOfAKind_Aces",
     "FourOfAKind",
     ["AceOfSpades", "AceOfHearts", "AceOfDiamonds", "AceOfClubs", "KingOfSpades"]),

    ("Hand_FourOfAKind_Fives",
     "FourOfAKind",
     ["FiveOfSpades", "FiveOfHearts", "FiveOfDiamonds", "FiveOfClubs", "NineOfHearts"]),

    # --- Full House (2) ---
    ("Hand_FullHouse_KingsJacks",
     "FullHouse",
     ["KingOfSpades", "KingOfHearts", "KingOfDiamonds", "JackOfSpades", "JackOfClubs"]),

    ("Hand_FullHouse_ThreesSevens",
     "FullHouse",
     ["ThreeOfSpades", "ThreeOfHearts", "ThreeOfClubs", "SevenOfDiamonds", "SevenOfHearts"]),

    # --- Flush (2) ---
    ("Hand_Flush_Diamonds",
     "Flush",
     ["AceOfDiamonds", "SixOfDiamonds", "NineOfDiamonds", "ThreeOfDiamonds", "JackOfDiamonds"]),

    ("Hand_Flush_Clubs",
     "Flush",
     ["TwoOfClubs", "SevenOfClubs", "EightOfClubs", "QueenOfClubs", "KingOfClubs"]),

    # --- Straight (3: wheel, middle, broadway) ---
    ("Hand_Straight_Wheel",
     "Straight",
     ["AceOfSpades", "TwoOfHearts", "ThreeOfDiamonds", "FourOfClubs", "FiveOfSpades"]),

    ("Hand_Straight_Middle",
     "Straight",
     ["FiveOfSpades", "SixOfHearts", "SevenOfDiamonds", "EightOfClubs", "NineOfSpades"]),

    ("Hand_Straight_Broadway",
     "Straight",
     ["TenOfSpades", "JackOfHearts", "QueenOfDiamonds", "KingOfClubs", "AceOfHearts"]),

    # --- Three of a Kind (2) ---
    ("Hand_ThreeOfAKind_Queens",
     "ThreeOfAKind",
     ["QueenOfSpades", "QueenOfHearts", "QueenOfDiamonds", "FiveOfClubs", "TwoOfHearts"]),

    ("Hand_ThreeOfAKind_Twos",
     "ThreeOfAKind",
     ["TwoOfSpades", "TwoOfHearts", "TwoOfDiamonds", "AceOfClubs", "KingOfHearts"]),

    # --- Two Pair (2) ---
    ("Hand_TwoPair_AcesKings",
     "TwoPair",
     ["AceOfSpades", "AceOfHearts", "KingOfDiamonds", "KingOfClubs", "TwoOfSpades"]),

    ("Hand_TwoPair_TensFours",
     "TwoPair",
     ["TenOfSpades", "TenOfHearts", "FourOfDiamonds", "FourOfClubs", "JackOfSpades"]),

    # --- One Pair (2) ---
    ("Hand_OnePair_Sevens",
     "OnePair",
     ["SevenOfSpades", "SevenOfHearts", "AceOfDiamonds", "KingOfClubs", "TwoOfSpades"]),

    ("Hand_OnePair_Jacks",
     "OnePair",
     ["JackOfSpades", "JackOfClubs", "NineOfDiamonds", "FiveOfHearts", "ThreeOfSpades"]),

    # --- High Card (2) ---
    ("Hand_HighCard_AceHigh",
     "HighCard",
     ["AceOfSpades", "JackOfHearts", "NineOfDiamonds", "FiveOfClubs", "TwoOfSpades"]),

    ("Hand_HighCard_KingHigh",
     "HighCard",
     ["KingOfHearts", "TenOfDiamonds", "EightOfClubs", "SixOfSpades", "ThreeOfHearts"]),
]

# ══════════════════════════════════════════════════════════════════
# BLOCK 2: Hands WITHOUT ranking (inference test)
# Only cards are assigned. The reasoner must infer the hand type
# through the Module 13 XxxByCardsBestHand patterns.
# ══════════════════════════════════════════════════════════════════
INFER_HANDS = [
    # Expected: RoyalFlushByCardsBestHand
    ("Hand_Infer_RoyalFlush",
     "RoyalFlush",
     ["TenOfDiamonds", "JackOfDiamonds", "QueenOfDiamonds", "KingOfDiamonds", "AceOfDiamonds"]),

    # Expected: SteelWheelBestHand
    ("Hand_Infer_SteelWheel",
     "StraightFlush",
     ["AceOfClubs", "TwoOfClubs", "ThreeOfClubs", "FourOfClubs", "FiveOfClubs"]),

    # Expected: FourOfAKindByCardsBestHand
    ("Hand_Infer_FourOfAKind",
     "FourOfAKind",
     ["KingOfSpades", "KingOfHearts", "KingOfDiamonds", "KingOfClubs", "TwoOfDiamonds"]),

    # Expected: FullHouseByCardsBestHand (also ThreeOfAKind, TwoPair, OnePair by cards)
    ("Hand_Infer_FullHouse",
     "FullHouse",
     ["EightOfSpades", "EightOfHearts", "EightOfDiamonds", "FourOfSpades", "FourOfHearts"]),

    # Expected: FlushByCardsBestHand
    ("Hand_Infer_Flush",
     "Flush",
     ["TwoOfHearts", "FiveOfHearts", "EightOfHearts", "JackOfHearts", "AceOfHearts"]),

    # Expected: StraightByRanksBestHand
    ("Hand_Infer_Straight",
     "Straight",
     ["SixOfSpades", "SevenOfHearts", "EightOfDiamonds", "NineOfClubs", "TenOfSpades"]),

    # Expected: ThreeOfAKindByCardsBestHand (also OnePair by cards)
    ("Hand_Infer_ThreeOfAKind",
     "ThreeOfAKind",
     ["NineOfSpades", "NineOfHearts", "NineOfClubs", "AceOfDiamonds", "FourOfSpades"]),

    # Expected: TwoPairByCardsBestHand (also OnePair by cards)
    ("Hand_Infer_TwoPair",
     "TwoPair",
     ["SixOfSpades", "SixOfHearts", "QueenOfDiamonds", "QueenOfClubs", "ThreeOfSpades"]),

    # Expected: OnePairByCardsBestHand
    ("Hand_Infer_OnePair",
     "OnePair",
     ["ThreeOfSpades", "ThreeOfDiamonds", "KingOfClubs", "JackOfHearts", "FiveOfSpades"]),

    # Expected: HighCardByCardsBestHand (complement: no pair, straight, or flush)
    ("Hand_Infer_HighCard",
     "HighCard",
     ["AceOfClubs", "TenOfHearts", "EightOfSpades", "SixOfDiamonds", "ThreeOfClubs"]),
]

# ══════════════════════════════════════════════════════════════════
# BLOCK 3: Invalid / edge-case hands (inconsistency test)
# These are expected to cause inconsistency or remain unclassified.
# Load them SEPARATELY in Protege to test one at a time.
# ══════════════════════════════════════════════════════════════════
INVALID_HANDS = [
    # Wrong ranking: cards form a Flush but ranking says OnePair
    # Expected: inconsistency when reasoner runs
    ("Hand_Invalid_WrongRanking",
     "OnePair",
     ["AceOfSpades", "SixOfSpades", "NineOfSpades", "ThreeOfSpades", "JackOfSpades"]),

    # Incomplete hand: only 3 cards assigned
    # Expected: not classified as any XxxByCardsBestHand
    ("Hand_Invalid_Incomplete",
     None,
     ["AceOfSpades", "KingOfSpades", "QueenOfSpades"]),

    # Wrong ranking: cards form a Straight but ranking says HighCard
    # Expected: inconsistency when reasoner runs
    ("Hand_Invalid_StraightAsHighCard",
     "HighCard",
     ["FiveOfHearts", "SixOfDiamonds", "SevenOfClubs", "EightOfSpades", "NineOfHearts"]),
]


def generate():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    lines = []

    def w(text=""):
        lines.append(text)

    # Prefixes
    w("@prefix poker: <http://www.poker-ontology.org/poker#> .")
    w("@prefix owl:   <http://www.w3.org/2002/07/owl#> .")
    w("@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    w("@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .")
    w("@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .")
    w()
    w("# ============================================================")
    w("# ABOX: Poker hand instances for testing with OWL 2 DL reasoners")
    w("# Imports TBox: poker_complete_ontology.ttl")
    w("# ============================================================")
    w("# Block 1: Hands WITH explicit hasHandRanking  (coherence test)")
    w("# Block 2: Hands WITHOUT hasHandRanking         (inference test)")
    w("# Block 3: Invalid / edge-case hands            (inconsistency test)")
    w("# ============================================================")
    w("# The reasoner (HermiT/Pellet) should:")
    w("#   Block 1 → confirm consistency and classify into XxxBestHand")
    w("#   Block 2 → infer XxxByCardsBestHand from card patterns alone")
    w("#   Block 3 → detect inconsistency or leave unclassified")
    w("# ============================================================")
    w()
    w("<http://www.poker-ontology.org/abox>")
    w("    rdf:type owl:Ontology ;")
    w('    owl:imports <http://www.poker-ontology.org/poker> ;')
    w('    rdfs:label "ABox: Poker Hand Test Instances" ;')
    w('    rdfs:comment "Instance layer with 35 test hands for OWL 2 DL reasoning." .')
    w()

    # ── Block 1: Explicit ranking ──────────────────────────────────
    w("# ============================================================")
    w("# BLOCK 1: Hands with explicit ranking (coherence test)")
    w("# ============================================================")
    w()

    all_hand_names = []
    for name, hand_type, cards in EXPLICIT_HANDS:
        ranking_ind = HAND_RANKINGS[hand_type]
        w(f"# {hand_type}: {', '.join(cards)}")
        w(f"poker:{name} a poker:BestHand ;")
        for card in cards:
            w(f"    poker:containsCard poker:{card} ;")
        w(f"    poker:hasHandRanking poker:{ranking_ind} ;")
        w(f'    rdfs:label "{name}" .')
        w()
        all_hand_names.append(name)

    # ── Block 2: Inference test ────────────────────────────────────
    w("# ============================================================")
    w("# BLOCK 2: Hands WITHOUT ranking (inference test)")
    w("# Only containsCard is asserted. The reasoner should infer")
    w("# the hand type via Module 13 XxxByCardsBestHand patterns.")
    w("# ============================================================")
    w()

    for name, expected_type, cards in INFER_HANDS:
        w(f"# Expected inference: {expected_type}")
        w(f"poker:{name} a poker:BestHand ;")
        for card in cards:
            w(f"    poker:containsCard poker:{card} ;")
        w(f'    rdfs:label "{name}" .')
        w()
        all_hand_names.append(name)

    # ── Block 3: Invalid / edge cases ─────────────────────────────
    w("# ============================================================")
    w("# BLOCK 3: Invalid / edge-case hands (inconsistency test)")
    w("# WARNING: These may cause the reasoner to detect inconsistency.")
    w("# Load separately or comment out to test blocks 1-2 first.")
    w("# ============================================================")
    w()

    for name, hand_type, cards in INVALID_HANDS:
        if hand_type is not None:
            ranking_ind = HAND_RANKINGS[hand_type]
            w(f"# INVALID: cards do not match ranking '{hand_type}'")
            w(f"poker:{name} a poker:BestHand ;")
            for card in cards:
                w(f"    poker:containsCard poker:{card} ;")
            w(f"    poker:hasHandRanking poker:{ranking_ind} ;")
            w(f'    rdfs:label "{name}" .')
        else:
            w(f"# EDGE CASE: incomplete hand ({len(cards)} cards)")
            w(f"poker:{name} a poker:BestHand ;")
            for card in cards:
                w(f"    poker:containsCard poker:{card} ;")
            w(f'    rdfs:label "{name}" .')
        w()
        all_hand_names.append(name)

    # AllDifferent over all hand individuals
    w("# ============================================================")
    w("# All hand individuals are distinct from each other")
    w("# ============================================================")
    w("[] a owl:AllDifferent ;")
    w("    owl:distinctMembers (")
    for name in all_hand_names:
        w(f"        poker:{name}")
    w("    ) .")

    # Write file
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")

    total = len(EXPLICIT_HANDS) + len(INFER_HANDS) + len(INVALID_HANDS)
    print(f"Done. ABox written to {OUTPUT}")
    print(f"  Block 1 (explicit ranking): {len(EXPLICIT_HANDS)} hands")
    print(f"  Block 2 (inference test):   {len(INFER_HANDS)} hands")
    print(f"  Block 3 (invalid/edge):     {len(INVALID_HANDS)} hands")
    print(f"  Total:                      {total} hands")


if __name__ == "__main__":
    generate()
