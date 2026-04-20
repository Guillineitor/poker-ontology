#!/usr/bin/env python3
"""Generate the Texas Hold'em Poker Ontology (English version) in OWL 2 DL / Turtle.
Includes the hand inference layer in addition to the base ontology.
The resulting ontology allows OWL 2 DL reasoners (HermiT/Pellet/FaCT++)
to automatically classify poker hands given their 5 explicit cards."""

import os
from itertools import combinations

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "ontology", "poker_complete_ontology.ttl")

# === Constants ===
RANKS = ["Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
         "Nine", "Ten", "Jack", "Queen", "King", "Ace"]
SUITS = ["Spades", "Hearts", "Diamonds", "Clubs"]

RANK_VALUES = {
    "Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7,
    "Eight": 8, "Nine": 9, "Ten": 10, "Jack": 11, "Queen": 12, "King": 13, "Ace": 14
}

# Straight rank index combos (indices into RANKS)
STRAIGHTS = [
    [12, 0, 1, 2, 3],    # Wheel: A-2-3-4-5
    [0, 1, 2, 3, 4],     # 6-high: 2-3-4-5-6
    [1, 2, 3, 4, 5],     # 7-high: 3-4-5-6-7
    [2, 3, 4, 5, 6],     # 8-high: 4-5-6-7-8
    [3, 4, 5, 6, 7],     # 9-high: 5-6-7-8-9
    [4, 5, 6, 7, 8],     # 10-high: 6-7-8-9-10
    [5, 6, 7, 8, 9],     # J-high: 7-8-9-10-J
    [6, 7, 8, 9, 10],    # Q-high: 8-9-10-J-Q
    [7, 8, 9, 10, 11],   # K-high: 9-10-J-Q-K
    [8, 9, 10, 11, 12],  # A-high (Broadway): 10-J-Q-K-A
]


def ciri(rank, suit):
    """Card IRI like poker:TwoOfSpades"""
    return f"poker:{rank}Of{suit}"


def clabel(rank, suit):
    """Card label in English"""
    return f"{rank} of {suit}"


# ── Builder ────────────────────────────────────────────────────────
lines = []


def w(text=""):
    lines.append(text)


def blank():
    w()


def comment(text):
    w(f"# {text}")


def section(title):
    blank()
    w("# " + "=" * 60)
    w(f"# {title}")
    w("# " + "=" * 60)
    blank()


# === hasValue restriction shorthand ===
def has_value_restriction(prop, individual):
    return (f"[ a owl:Restriction ; owl:onProperty poker:{prop} ; "
            f"owl:hasValue poker:{individual} ]")


def qualified_card_restriction(prop, n, on_class, kind="qualifiedCardinality"):
    return (f"[ a owl:Restriction ; owl:onProperty poker:{prop} ; "
            f'owl:{kind} "{n}"^^xsd:nonNegativeInteger ; '
            f"owl:onClass poker:{on_class} ]")


# ── Module 13 helpers ──────────────────────────────────────────────

def hv_card_r(card_iri):
    """owl:hasValue restriction on containsCard for a specific card individual."""
    return (f"[ a owl:Restriction ; owl:onProperty poker:containsCard ; "
            f"owl:hasValue poker:{card_iri} ]")


def qc_rank_r(rank, n, kind="qualifiedCardinality"):
    """qualifiedCardinality restriction on containsCard for a rank helper class."""
    return (f"[ a owl:Restriction ; owl:onProperty poker:containsCard ; "
            f"owl:{kind} \"{n}\"^^xsd:nonNegativeInteger ; "
            f"owl:onClass poker:{rank}RankCard ]")


def qc_suit_r(suit, n, kind="qualifiedCardinality"):
    """qualifiedCardinality restriction on containsCard for a suit helper class."""
    return (f"[ a owl:Restriction ; owl:onProperty poker:containsCard ; "
            f"owl:{kind} \"{n}\"^^xsd:nonNegativeInteger ; "
            f"owl:onClass poker:{suit}Card ]")


def write_m13_union_equiv(class_name, members, label, cmt):
    """Write: poker:{class_name} ≡ BestHand ∩ unionOf(members).

    Each element of `members` is either:
    - str  → written directly as one union alternative
    - list → wrapped in owl:intersectionOf as one union alternative
    """
    w(f"poker:{class_name} a owl:Class ;")
    w( "    owl:equivalentClass [")
    w( "        a owl:Class ;")
    w( "        owl:intersectionOf (")
    w( "            poker:BestHand")
    w( "            [ a owl:Class ;")
    w( "              owl:unionOf (")
    for m in members:
        if isinstance(m, str):
            w(f"                {m}")
        elif len(m) == 1:
            w(f"                {m[0]}")
        else:
            w( "                [ a owl:Class ; owl:intersectionOf (")
            for part in m:
                w(f"                    {part}")
            w( "                )]")
    w( "              )")
    w( "            ]")
    w( "        )")
    w( "    ] ;")
    w(f"    rdfs:label \"{label}\" ;")
    w(f"    rdfs:comment \"{cmt}\" .")
    blank()


# ══════════════════════════════════════════════════════════════════
#  MAIN GENERATION
# ══════════════════════════════════════════════════════════════════
def generate():

    # ================================================================
    # MODULE 1 – Prefixes & Ontology declaration
    # ================================================================
    section("MODULE 1: Prefixes and Ontology Declaration")

    w("@prefix : <http://www.poker-ontology.org/poker#> .")
    w("@prefix poker: <http://www.poker-ontology.org/poker#> .")
    w("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
    w("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .")
    w("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    w("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    blank()

    w("# ============================================================")
    w("# COMPLETE ONTOLOGY: TEXAS HOLD'EM POKER (with Module 13)")
    w("# Profile: OWL 2 DL  |  Serialization: Turtle (.ttl)")
    w("# Namespace: http://www.poker-ontology.org/poker#")
    w("# Version: 2.1.0  (base + hand inference layer)")
    w("# ============================================================")
    w("# PURPOSE:")
    w("#   COMPLETE ontology that includes the structural vocabulary")
    w("#   (Modules 1-12) and the hand inference layer (Module 13).")
    w("#   Module 13 defines owl:equivalentClass patterns that allow")
    w("#   an OWL 2 DL reasoner to automatically classify hands")
    w("#   given that their 5 cards are explicitly assigned.")
    w("# ============================================================")
    w("# OPEN WORLD ASSUMPTION (OWA):")
    w("#   OWL operates under OWA: what is not asserted is unknown, not false.")
    w("#   To mitigate this, Suit and Rank are closed with owl:oneOf, and the")
    w("#   52 card individuals are declared AllDifferent.")
    w("#   Module 13 inference patterns require all cards in a BestHand")
    w("#   to be explicitly assigned.")
    w("# ============================================================")
    blank()
    w("<http://www.poker-ontology.org/poker>")
    w("    rdf:type owl:Ontology ;")
    w('    rdfs:label "Poker Ontology (Complete)" ;')
    w('    rdfs:comment "Complete OWL 2 DL ontology with hand inference layer for Texas Hold\'em." ;')
    w('    owl:versionInfo "2.1.0" .')

    # ================================================================
    # MODULE 2 – The Deck (Card, Suit, Rank, Deck)
    # ================================================================
    section("MODULE 2: The Deck (Card, Suit, Rank, Deck)")

    w("# CLOSED CLASSES WITH owl:oneOf")
    w("# Suit and Rank are defined with owl:equivalentClass + owl:oneOf to")
    w("# close the world over suits and ranks. Without this, OWL would allow")
    w("# the existence of a 5th undeclared suit (Open World Assumption).")
    w("# With oneOf we guarantee:")
    w("#   Suit ≡ {Spades, Hearts, Diamonds, Clubs}  (exactly 4 suits)")
    w("#   Rank ≡ {Two, Three, ..., Ace}              (exactly 13 ranks)")
    blank()
    # Suit (closed)
    w("poker:Suit a owl:Class ;")
    w("    owl:equivalentClass [")
    w("        a owl:Class ;")
    w("        owl:oneOf ( poker:Spades poker:Hearts poker:Diamonds poker:Clubs )")
    w("    ] ;")
    w('    rdfs:label "Suit" ;')
    w('    rdfs:comment "Suit of a card. Closed class: exactly Spades, Hearts, Diamonds, Clubs." .')
    blank()

    # Rank (closed)
    rank_list = " ".join(f"poker:{r}" for r in RANKS)
    w("poker:Rank a owl:Class ;")
    w("    owl:equivalentClass [")
    w("        a owl:Class ;")
    w(f"        owl:oneOf ( {rank_list} )")
    w("    ] ;")
    w('    rdfs:label "Rank" ;')
    w('    rdfs:comment "Rank of a card. Closed class: exactly 13 values from Two to Ace." .')
    blank()

    # Card
    w("poker:Card a owl:Class ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ;")
    w("        owl:onProperty poker:hasSuit ;")
    w("        owl:someValuesFrom poker:Suit")
    w("    ] ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ;")
    w("        owl:onProperty poker:hasRank ;")
    w("        owl:someValuesFrom poker:Rank")
    w("    ] ;")
    w('    rdfs:label "Card" ;')
    w('    rdfs:comment "A card from the standard 52-card deck." .')
    blank()

    # Deck
    w("poker:Deck a owl:Class ;")
    w('    rdfs:label "Deck" ;')
    w('    rdfs:comment "A complete 52-card deck." .')

    # ================================================================
    # MODULE 3 – Hands and Community Cards
    # ================================================================
    section("MODULE 3: Hands and Community Cards")

    w("# HAND HIERARCHY:")
    w("#   Hand")
    w("#   ├── HoleCards       (= 2 cards)  player's private cards")
    w("#   ├── CommunityCards               shared cards")
    w("#   │     ├── Flop     (= 3 cards)  first 3 community cards")
    w("#   │     ├── Turn     (= 1 card)   4th community card")
    w("#   │     └── River    (= 1 card)   5th community card")
    w("#   └── BestHand       (= 5 cards)  player's best combination")
    w("# Cardinalities are implemented with owl:qualifiedCardinality.")
    w("# BestHand also requires hasHandRanking someValuesFrom HandRanking.")
    blank()
    w("poker:Hand a owl:Class ;")
    w('    rdfs:label "Hand" ;')
    w('    rdfs:comment "A hand of cards in the game." .')
    blank()

    # HoleCards
    w("poker:HoleCards a owl:Class ;")
    w("    rdfs:subClassOf poker:Hand ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ;")
    w("        owl:onProperty poker:containsCard ;")
    w('        owl:qualifiedCardinality "2"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Card")
    w("    ] ;")
    w('    rdfs:label "Hole Cards" ;')
    w('    rdfs:comment "The 2 private cards dealt to each player." .')
    blank()

    # CommunityCards
    w("poker:CommunityCards a owl:Class ;")
    w("    rdfs:subClassOf poker:Hand ;")
    w('    rdfs:label "Community Cards" ;')
    w('    rdfs:comment "The community cards shared by all players." .')
    blank()

    # Flop
    w("poker:Flop a owl:Class ;")
    w("    rdfs:subClassOf poker:CommunityCards ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ;")
    w("        owl:onProperty poker:containsCard ;")
    w('        owl:qualifiedCardinality "3"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Card")
    w("    ] ;")
    w('    rdfs:label "Flop" ;')
    w('    rdfs:comment "The first 3 community cards." .')
    blank()

    # Turn
    w("poker:Turn a owl:Class ;")
    w("    rdfs:subClassOf poker:CommunityCards ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ;")
    w("        owl:onProperty poker:containsCard ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Card")
    w("    ] ;")
    w('    rdfs:label "Turn" ;')
    w('    rdfs:comment "The 4th community card." .')
    blank()

    # River
    w("poker:River a owl:Class ;")
    w("    rdfs:subClassOf poker:CommunityCards ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ;")
    w("        owl:onProperty poker:containsCard ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Card")
    w("    ] ;")
    w('    rdfs:label "River" ;')
    w('    rdfs:comment "The 5th and final community card." .')
    blank()

    # BestHand
    w("poker:BestHand a owl:Class ;")
    w("    rdfs:subClassOf poker:Hand ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ;")
    w("        owl:onProperty poker:containsCard ;")
    w('        owl:qualifiedCardinality "5"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Card")
    w("    ] ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ;")
    w("        owl:onProperty poker:hasHandRanking ;")
    w("        owl:someValuesFrom poker:HandRanking")
    w("    ] ;")
    w('    rdfs:label "Best Hand" ;')
    w('    rdfs:comment "The best 5-card combination of a player." .')

    # ================================================================
    # MODULE 4 – Hand Rankings
    # ================================================================
    section("MODULE 4: Hand Rankings (HandRanking)")

    w("# RANKING HIERARCHY (from lowest to highest strength):")
    w("#   HandRanking")
    w("#   ├── HighCard       (1) highest card — no combination")
    w("#   ├── OnePair        (2) two cards of the same rank")
    w("#   ├── TwoPair        (3) two distinct pairs")
    w("#   ├── ThreeOfAKind   (4) three cards of the same rank")
    w("#   ├── Straight       (5) five consecutive cards, different suits")
    w("#   ├── Flush          (6) five cards of the same suit")
    w("#   ├── FullHouse      (7) three of a kind plus a pair")
    w("#   ├── FourOfAKind    (8) four cards of the same rank")
    w("#   └── StraightFlush  (9) five consecutive cards of the same suit")
    w("#         └── RoyalFlush   10-J-Q-K-A of the same suit (subclass of StraightFlush)")
    w("#")
    w("# NOTE: RoyalFlush is a SUBCLASS of StraightFlush, not disjoint.")
    w("# The 9 base classes are AllDisjoint among themselves (see Module 11).")
    blank()
    w("poker:HandRanking a owl:Class ;")
    w('    rdfs:label "Hand Ranking" ;')
    w('    rdfs:comment "Ranking category for a poker hand." .')
    blank()

    hr_classes = [
        ("HighCard",      "High Card",       "No combination; the highest card decides."),
        ("OnePair",       "One Pair",        "Two cards of the same rank."),
        ("TwoPair",       "Two Pair",        "Two distinct pairs."),
        ("ThreeOfAKind",  "Three of a Kind", "Three cards of the same rank."),
        ("Straight",      "Straight",        "Five consecutive cards of different suits."),
        ("Flush",         "Flush",           "Five cards of the same suit."),
        ("FullHouse",     "Full House",      "Three of a kind plus a pair."),
        ("FourOfAKind",   "Four of a Kind",  "Four cards of the same rank."),
        ("StraightFlush", "Straight Flush",  "Five consecutive cards of the same suit."),
    ]

    for cls, label, cmt in hr_classes:
        w(f"poker:{cls} a owl:Class ;")
        w(f"    rdfs:subClassOf poker:HandRanking ;")
        w(f'    rdfs:label "{label}" ;')
        w(f'    rdfs:comment "{cmt}" .')
        blank()

    # RoyalFlush ⊂ StraightFlush
    w("poker:RoyalFlush a owl:Class ;")
    w("    rdfs:subClassOf poker:StraightFlush ;")
    w('    rdfs:label "Royal Flush" ;')
    w('    rdfs:comment "Straight flush from Ten to Ace (10-J-Q-K-A of the same suit)." .')

    # ================================================================
    # MODULE 5 – Players, Positions, Roles
    # ================================================================
    section("MODULE 5: Players, Positions, and Roles")

    w("# DEFINED ROLE CLASSES (owl:equivalentClass):")
    w("# Dealer, SmallBlindPlayer, and BigBlindPlayer are DEFINED classes:")
    w("#   Dealer           ≡ Player ∩ hasPosition.{Button}")
    w("#   SmallBlindPlayer ≡ Player ∩ hasPosition.{SmallBlind}")
    w("#   BigBlindPlayer   ≡ Player ∩ hasPosition.{BigBlind}")
    w("# A reasoner automatically infers the player's role")
    w("# based on their position, without explicit declaration.")
    w("#")
    w("# HEADS-UP NOTE: ButtonPosition is NOT disjoint with")
    w("# SmallBlindPosition because in heads-up (2 players)")
    w("# the Button IS the Small Blind. See Module 11.")
    blank()
    w("poker:Player a owl:Class ;")
    w('    rdfs:label "Player" ;')
    w('    rdfs:comment "A poker player." .')
    blank()

    w("poker:Position a owl:Class ;")
    w('    rdfs:label "Position" ;')
    w('    rdfs:comment "A player\'s position at the table." .')
    blank()

    positions = [
        ("SmallBlindPosition", "Small Blind Position", "Position of the player who posts the small blind."),
        ("BigBlindPosition",   "Big Blind Position",   "Position of the player who posts the big blind."),
        ("EarlyPosition",      "Early Position",       "Early position (Under the Gun)."),
        ("MiddlePosition",     "Middle Position",      "Middle position at the table."),
        ("LatePosition",       "Late Position",        "Late position (Cutoff)."),
        ("ButtonPosition",     "Button Position",      "Dealer (button) position."),
    ]

    for cls, label, cmt in positions:
        w(f"poker:{cls} a owl:Class ;")
        w(f"    rdfs:subClassOf poker:Position ;")
        w(f'    rdfs:label "{label}" ;')
        w(f'    rdfs:comment "{cmt}" .')
        blank()

    # Defined role classes
    defined_roles = [
        ("Dealer",           "Button",     "Dealer",              "Player with the button (dealer) position. Defined class."),
        ("SmallBlindPlayer", "SmallBlind", "Small Blind Player",  "Player in the small blind position. Defined class."),
        ("BigBlindPlayer",   "BigBlind",   "Big Blind Player",    "Player in the big blind position. Defined class."),
    ]

    for cls, pos_ind, label, cmt in defined_roles:
        w(f"poker:{cls} a owl:Class ;")
        w( "    owl:equivalentClass [")
        w( "        a owl:Class ;")
        w( "        owl:intersectionOf (")
        w( "            poker:Player")
        w(f"            {has_value_restriction('hasPosition', pos_ind)}")
        w( "        )")
        w( "    ] ;")
        w(f'    rdfs:label "{label}" ;')
        w(f'    rdfs:comment "{cmt}" .')
        blank()

    # ================================================================
    # MODULE 6 – Game Structure
    # ================================================================
    section("MODULE 6: Game Structure (Game, Round)")

    w("# Game is the central class that connects all elements.")
    w("# STRUCTURAL RESTRICTIONS OF A GAME:")
    w("#   - Between 2 and 10 players (minQC 2, maxQC 10)")
    w("#   - Exactly 1 round of each type (PreFlop/Flop/Turn/River/Showdown)")
    w("#   - Exactly 1 Flop, 1 Turn, 1 River community (hasCommunityCards)")
    w("#   - At least 1 MainPot (hasPot minQC 1)")
    w("#   - At least 1 winner (hasWinner minQC 1)")
    w("# PreFlop requires mandatory PostSmallBlind and PostBigBlind actions.")
    w("# Showdown has maxQC 0 actions: no betting occurs at showdown.")
    w("# HeadsUpGame is a DEFINED class: Game ∩ (=2 players) ∩ isHeadsUp=true.")
    blank()
    w("poker:Game a owl:Class ;")
    w('    rdfs:label "Game" ;')
    w('    rdfs:comment "A Texas Hold\'em Poker game." ;')
    # 2-10 players
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasPlayer ;")
    w('        owl:minQualifiedCardinality "2"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Player")
    w("    ] ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasPlayer ;")
    w('        owl:maxQualifiedCardinality "10"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Player")
    w("    ] ;")
    # 1 PreFlop
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasRound ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:PreFlop")
    w("    ] ;")
    # 1 FlopRound
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasRound ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:FlopRound")
    w("    ] ;")
    # 1 TurnRound
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasRound ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:TurnRound")
    w("    ] ;")
    # 1 RiverRound
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasRound ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:RiverRound")
    w("    ] ;")
    # 1 Showdown
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasRound ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Showdown")
    w("    ] ;")
    # 1 Flop community
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasCommunityCards ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Flop")
    w("    ] ;")
    # 1 Turn community
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasCommunityCards ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Turn")
    w("    ] ;")
    # 1 River community
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasCommunityCards ;")
    w('        owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:River")
    w("    ] ;")
    # ≥1 MainPot
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasPot ;")
    w('        owl:minQualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:MainPot")
    w("    ] ;")
    # ≥1 winner
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasWinner ;")
    w('        owl:minQualifiedCardinality "1"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Player")
    w("    ] .")
    blank()

    # HeadsUpGame
    w("poker:HeadsUpGame a owl:Class ;")
    w("    owl:equivalentClass [")
    w("        a owl:Class ;")
    w("        owl:intersectionOf (")
    w("            poker:Game")
    w("            [ a owl:Restriction ; owl:onProperty poker:hasPlayer ;")
    w('              owl:qualifiedCardinality "2"^^xsd:nonNegativeInteger ;')
    w("              owl:onClass poker:Player ]")
    w("            [ a owl:Restriction ; owl:onProperty poker:isHeadsUp ;")
    w('              owl:hasValue "true"^^xsd:boolean ]')
    w("        )")
    w("    ] ;")
    w('    rdfs:label "Heads-Up Game" ;')
    w('    rdfs:comment "Heads-up game (exactly 2 players)." .')
    blank()

    # Round
    w("poker:Round a owl:Class ;")
    w('    rdfs:label "Round" ;')
    w('    rdfs:comment "A round of play in a poker game." .')
    blank()

    # PreFlop (with blind requirements)
    w("poker:PreFlop a owl:Class ;")
    w("    rdfs:subClassOf poker:Round ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasAction ;")
    w("        owl:someValuesFrom poker:PostSmallBlind")
    w("    ] ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasAction ;")
    w("        owl:someValuesFrom poker:PostBigBlind")
    w("    ] ;")
    w('    rdfs:label "PreFlop" ;')
    w('    rdfs:comment "First betting round, before community cards. Includes mandatory blinds." .')
    blank()

    for cls, label, cmt in [("FlopRound", "Flop Round", "Betting round after the Flop."),
                             ("TurnRound", "Turn Round", "Betting round after the Turn."),
                             ("RiverRound", "River Round", "Betting round after the River.")]:
        w(f"poker:{cls} a owl:Class ;")
        w(f"    rdfs:subClassOf poker:Round ;")
        w(f'    rdfs:label "{label}" ;')
        w(f'    rdfs:comment "{cmt}" .')
        blank()

    # Showdown (0 actions)
    w("poker:Showdown a owl:Class ;")
    w("    rdfs:subClassOf poker:Round ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:hasAction ;")
    w('        owl:maxQualifiedCardinality "0"^^xsd:nonNegativeInteger ;')
    w("        owl:onClass poker:Action")
    w("    ] ;")
    w('    rdfs:label "Showdown" ;')
    w('    rdfs:comment "Final round where hands are compared. No betting." .')

    # ================================================================
    # MODULE 7 – Actions and Bets
    # ================================================================
    section("MODULE 7: Actions and Bets")

    w("# ACTION HIERARCHY:")
    w("#   Action")
    w("#   ├── Fold        withdraw from the hand")
    w("#   ├── Check       pass without betting (only if no prior bet)")
    w("#   ├── Call        match the current bet")
    w("#   ├── Bet         place a new bet")
    w("#   ├── Raise       increase an existing bet")
    w("#   ├── AllIn       bet all chips (abstract class)")
    w("#   │     ├── AllInBet    subClassOf AllIn ∩ Bet")
    w("#   │     ├── AllInCall   subClassOf AllIn ∩ Call")
    w("#   │     └── AllInRaise  subClassOf AllIn ∩ Raise")
    w("#   └── PostBlind   mandatory blind (not voluntary)")
    w("#         ├── PostSmallBlind  only in PreFlop, by SmallBlindPlayer")
    w("#         └── PostBigBlind    only in PreFlop, by BigBlindPlayer")
    blank()
    # Action (with allValuesFrom restriction)
    w("poker:Action a owl:Class ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:performedIn ;")
    w("        owl:allValuesFrom [")
    w("            a owl:Class ;")
    w("            owl:unionOf ( poker:PreFlop poker:FlopRound poker:TurnRound poker:RiverRound )")
    w("        ]")
    w("    ] ;")
    w('    rdfs:label "Action" ;')
    w('    rdfs:comment "An action performed by a player during a betting round." .')
    blank()

    base_actions = [
        ("Fold",  "Fold",  "Withdraw from the hand."),
        ("Check", "Check", "Pass without betting."),
        ("Call",  "Call",  "Match the current bet."),
        ("Bet",   "Bet",   "Place a bet."),
        ("Raise", "Raise", "Increase the bet."),
    ]
    for cls, label, cmt in base_actions:
        w(f"poker:{cls} a owl:Class ;")
        w(f"    rdfs:subClassOf poker:Action ;")
        w(f'    rdfs:label "{label}" ;')
        w(f'    rdfs:comment "{cmt}" .')
        blank()

    # AllIn
    w("poker:AllIn a owl:Class ;")
    w("    rdfs:subClassOf poker:Action ;")
    w('    rdfs:label "All-In" ;')
    w('    rdfs:comment "Bet all chips." .')
    blank()

    for cls, also, label, cmt in [("AllInBet",   "Bet",   "All-In Bet",   "All-in as a bet."),
                                   ("AllInCall",  "Call",  "All-In Call",  "All-in calling."),
                                   ("AllInRaise", "Raise", "All-In Raise", "All-in raising.")]:
        w(f"poker:{cls} a owl:Class ;")
        w(f"    rdfs:subClassOf poker:AllIn , poker:{also} ;")
        w(f'    rdfs:label "{label}" ;')
        w(f'    rdfs:comment "{cmt}" .')
        blank()

    # PostBlind hierarchy
    w("poker:PostBlind a owl:Class ;")
    w("    rdfs:subClassOf poker:Action ;")
    w('    rdfs:label "Post Blind" ;')
    w('    rdfs:comment "Mandatory blind bet." .')
    blank()

    # PostSmallBlind
    w("poker:PostSmallBlind a owl:Class ;")
    w("    rdfs:subClassOf poker:PostBlind ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:performedIn ;")
    w("        owl:someValuesFrom poker:PreFlop")
    w("    ] ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:performedBy ;")
    w("        owl:someValuesFrom poker:SmallBlindPlayer")
    w("    ] ;")
    w('    rdfs:label "Post Small Blind" ;')
    w('    rdfs:comment "Post the small blind (mandatory in PreFlop by the player in the small blind position)." .')
    blank()

    # PostBigBlind
    w("poker:PostBigBlind a owl:Class ;")
    w("    rdfs:subClassOf poker:PostBlind ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:performedIn ;")
    w("        owl:someValuesFrom poker:PreFlop")
    w("    ] ;")
    w("    rdfs:subClassOf [")
    w("        a owl:Restriction ; owl:onProperty poker:performedBy ;")
    w("        owl:someValuesFrom poker:BigBlindPlayer")
    w("    ] ;")
    w('    rdfs:label "Post Big Blind" ;')
    w('    rdfs:comment "Post the big blind (mandatory in PreFlop by the player in the big blind position)." .')

    # ================================================================
    # MODULE 8 – Pot, Table, Tournament
    # ================================================================
    section("MODULE 8: Pot, Table, Tournament")

    w("# POT HIERARCHY:")
    w("#   Pot")
    w("#   ├── MainPot   main pot (at least 1 per game)")
    w("#   └── SidePot   side pot (created when a player goes")
    w("#                 all-in for less than the total bet)")
    w("# MainPot and SidePot are disjoint (see Module 11).")
    blank()
    w("poker:Pot a owl:Class ;")
    w('    rdfs:label "Pot" ;')
    w('    rdfs:comment "The pot of chips in play." .')
    blank()

    w("poker:MainPot a owl:Class ;")
    w("    rdfs:subClassOf poker:Pot ;")
    w('    rdfs:label "Main Pot" ;')
    w('    rdfs:comment "The main pot of the game." .')
    blank()

    w("poker:SidePot a owl:Class ;")
    w("    rdfs:subClassOf poker:Pot ;")
    w('    rdfs:label "Side Pot" ;')
    w('    rdfs:comment "Side pot created when a player goes all-in." .')
    blank()

    w("poker:Table a owl:Class ;")
    w('    rdfs:label "Table" ;')
    w('    rdfs:comment "The poker table (physical or virtual)." .')
    blank()

    w("poker:Tournament a owl:Class ;")
    w('    rdfs:label "Tournament" ;')
    w('    rdfs:comment "A tournament that groups multiple games." .')
    blank()

    w("poker:Chip a owl:Class ;")
    w('    rdfs:label "Chip" ;')
    w('    rdfs:comment "Poker chip (monetary unit of the game)." .')
    blank()

    w("poker:BettingStructure a owl:Class ;")
    w('    rdfs:label "Betting Structure" ;')
    w('    rdfs:comment "Type of betting structure for the game." .')
    blank()

    for cls, label, cmt in [("NoLimitHoldEm",  "No Limit Hold'em",  "No limit betting structure."),
                             ("LimitHoldEm",    "Limit Hold'em",     "Fixed limit betting structure."),
                             ("PotLimitHoldEm", "Pot Limit Hold'em", "Pot limit betting structure.")]:
        w(f"poker:{cls} a owl:Class ;")
        w(f"    rdfs:subClassOf poker:BettingStructure ;")
        w(f'    rdfs:label "{label}" ;')
        w(f'    rdfs:comment "{cmt}" .')
        blank()

    # ================================================================
    # MODULE 9 – Object Properties
    # ================================================================
    section("MODULE 9: Object Properties")

    w("# ------------------------------------------------------------")
    w("# CARD PROPERTIES (Card → Suit / Rank)")
    w("# hasSuit and hasRank are FunctionalProperty: each card has")
    w("# exactly 1 suit and 1 rank (cannot change).")
    w("# ------------------------------------------------------------")
    blank()
    # hasSuit
    w("poker:hasSuit a owl:ObjectProperty , owl:FunctionalProperty ;")
    w("    rdfs:domain poker:Card ;")
    w("    rdfs:range poker:Suit ;")
    w('    rdfs:label "has suit" ;')
    w('    rdfs:comment "Associates a card with its suit." .')
    blank()

    # hasRank
    w("poker:hasRank a owl:ObjectProperty , owl:FunctionalProperty ;")
    w("    rdfs:domain poker:Card ;")
    w("    rdfs:range poker:Rank ;")
    w('    rdfs:label "has rank" ;')
    w('    rdfs:comment "Associates a card with its rank." .')
    blank()

    # containsCard
    w("poker:containsCard a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Hand ;")
    w("    rdfs:range poker:Card ;")
    w('    rdfs:label "contains card" ;')
    w('    rdfs:comment "Associates a hand with the cards it contains." .')
    blank()

    w("# ------------------------------------------------------------")
    w("# HAND PROPERTIES (Player ↔ Hand)")
    w("# ------------------------------------------------------------")
    blank()
    # hasHoleCards
    w("poker:hasHoleCards a owl:ObjectProperty , owl:FunctionalProperty , owl:InverseFunctionalProperty ;")
    w("    rdfs:domain poker:Player ;")
    w("    rdfs:range poker:HoleCards ;")
    w('    rdfs:label "has hole cards" ;')
    w('    rdfs:comment "Associates a player with their hole cards." .')
    blank()

    # hasBestHand
    w("poker:hasBestHand a owl:ObjectProperty , owl:FunctionalProperty ;")
    w("    rdfs:domain poker:Player ;")
    w("    rdfs:range poker:BestHand ;")
    w('    rdfs:label "has best hand" ;')
    w('    rdfs:comment "Associates a player with their best 5-card hand." .')
    blank()

    # hasHandRanking
    w("poker:hasHandRanking a owl:ObjectProperty , owl:FunctionalProperty ;")
    w("    rdfs:domain poker:BestHand ;")
    w("    rdfs:range poker:HandRanking ;")
    w('    rdfs:label "has hand ranking" ;')
    w('    rdfs:comment "Associates a best hand with its ranking category." .')
    blank()

    # isDealtTo
    w("poker:isDealtTo a owl:ObjectProperty , owl:FunctionalProperty ;")
    w("    rdfs:domain poker:Card ;")
    w("    rdfs:range poker:Player ;")
    w('    rdfs:label "is dealt to" ;')
    w('    rdfs:comment "Indicates which player a card was dealt to." .')
    blank()

    w("# ------------------------------------------------------------")
    w("# INVERSE PROPERTIES (Game ↔ Player / Action ↔ Round)")
    w("# ------------------------------------------------------------")
    blank()
    # hasPlayer / participatesIn  (inverses)
    w("poker:hasPlayer a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Game ;")
    w("    rdfs:range poker:Player ;")
    w("    owl:inverseOf poker:participatesIn ;")
    w('    rdfs:label "has player" ;')
    w('    rdfs:comment "Associates a game with a participating player." .')
    blank()

    w("poker:participatesIn a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Player ;")
    w("    rdfs:range poker:Game ;")
    w("    owl:inverseOf poker:hasPlayer ;")
    w('    rdfs:label "participates in" ;')
    w('    rdfs:comment "Associates a player with the game they participate in." .')
    blank()

    # hasWinner
    w("poker:hasWinner a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Game ;")
    w("    rdfs:range poker:Player ;")
    w('    rdfs:label "has winner" ;')
    w('    rdfs:comment "Associates a game with its winning player(s)." .')
    blank()

    # hasRound
    w("poker:hasRound a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Game ;")
    w("    rdfs:range poker:Round ;")
    w('    rdfs:label "has round" ;')
    w('    rdfs:comment "Associates a game with a round of play." .')
    blank()

    # hasPot
    w("poker:hasPot a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Game ;")
    w("    rdfs:range poker:Pot ;")
    w('    rdfs:label "has pot" ;')
    w('    rdfs:comment "Associates a game with a pot." .')
    blank()

    # hasSidePot (subPropertyOf hasPot)
    w("poker:hasSidePot a owl:ObjectProperty ;")
    w("    rdfs:subPropertyOf poker:hasPot ;")
    w("    rdfs:domain poker:Game ;")
    w("    rdfs:range poker:SidePot ;")
    w('    rdfs:label "has side pot" ;')
    w('    rdfs:comment "Associates a game with a side pot." .')
    blank()

    # hasCommunityCards
    w("poker:hasCommunityCards a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Game ;")
    w("    rdfs:range poker:CommunityCards ;")
    w('    rdfs:label "has community cards" ;')
    w('    rdfs:comment "Associates a game with its community cards." .')
    blank()

    # makesAction / performedBy  (inverses)
    w("poker:makesAction a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Player ;")
    w("    rdfs:range poker:Action ;")
    w("    owl:inverseOf poker:performedBy ;")
    w('    rdfs:label "makes action" ;')
    w('    rdfs:comment "Associates a player with an action they perform." .')
    blank()

    w("poker:performedBy a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Action ;")
    w("    rdfs:range poker:Player ;")
    w("    owl:inverseOf poker:makesAction ;")
    w('    rdfs:label "performed by" ;')
    w('    rdfs:comment "Indicates which player performed an action." .')
    blank()

    # performedIn / hasAction  (inverses)
    w("poker:performedIn a owl:ObjectProperty , owl:FunctionalProperty ;")
    w("    rdfs:domain poker:Action ;")
    w("    rdfs:range poker:Round ;")
    w("    owl:inverseOf poker:hasAction ;")
    w('    rdfs:label "performed in" ;')
    w('    rdfs:comment "Indicates in which round an action was performed." .')
    blank()

    w("poker:hasAction a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Round ;")
    w("    rdfs:range poker:Action ;")
    w("    owl:inverseOf poker:performedIn ;")
    w('    rdfs:label "has action" ;')
    w('    rdfs:comment "Associates a round with an action that occurred in it." .')
    blank()

    # hasPosition
    w("poker:hasPosition a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Player ;")
    w("    rdfs:range poker:Position ;")
    w('    rdfs:label "has position" ;')
    w('    rdfs:comment "Associates a player with their position at the table." .')
    blank()

    # usesStructure
    w("poker:usesStructure a owl:ObjectProperty , owl:FunctionalProperty ;")
    w("    rdfs:domain poker:Game ;")
    w("    rdfs:range poker:BettingStructure ;")
    w('    rdfs:label "uses structure" ;')
    w('    rdfs:comment "Associates a game with its betting structure." .')
    blank()

    # isPartOf
    w("poker:isPartOf a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Game ;")
    w("    rdfs:range poker:Tournament ;")
    w('    rdfs:label "is part of" ;')
    w('    rdfs:comment "Associates a game with the tournament it belongs to." .')
    blank()

    # hasTable
    w("poker:hasTable a owl:ObjectProperty , owl:FunctionalProperty ;")
    w("    rdfs:domain poker:Game ;")
    w("    rdfs:range poker:Table ;")
    w('    rdfs:label "has table" ;')
    w('    rdfs:comment "Associates a game with the table where it is played." .')
    blank()

    # winsHand
    w("poker:winsHand a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Player ;")
    w("    rdfs:range poker:BestHand ;")
    w('    rdfs:label "wins hand" ;')
    w('    rdfs:comment "Associates a player with the best hand they won with." .')
    blank()

    w("# ------------------------------------------------------------")
    w("# beats PROPERTY (TransitiveProperty)")
    w("# ------------------------------------------------------------")
    blank()
    # beats (Transitive)
    w("poker:beats a owl:ObjectProperty , owl:TransitiveProperty ;")
    w("    rdfs:domain poker:HandRanking ;")
    w("    rdfs:range poker:HandRanking ;")
    w('    rdfs:label "beats" ;')
    w('    rdfs:comment "Indicates that a hand ranking beats another. Transitive property." .')
    blank()

    # eligibleForPot
    w("poker:eligibleForPot a owl:ObjectProperty ;")
    w("    rdfs:domain poker:Player ;")
    w("    rdfs:range poker:Pot ;")
    w('    rdfs:label "eligible for pot" ;')
    w('    rdfs:comment "Indicates that a player is eligible to win a pot." .')

    # ================================================================
    # MODULE 10 – Data Properties
    # ================================================================
    section("MODULE 10: Data Properties")

    w("# Data Properties record scalar values from the domain.")
    w("# Those marked FunctionalProperty guarantee value uniqueness per individual.")
    blank()
    data_props = [
        ("hasRankValue",    "Rank",    "xsd:integer", True,  "has rank value",        "Numeric rank value (2-14)."),
        ("hasRankValueLow", "Rank",    "xsd:integer", True,  "has low rank value",    "Alternative low rank value (Ace only = 1)."),
        ("hasChipCount",    "Player",  "xsd:integer", False, "has chip count",        "Player's chip count."),
        ("hasBetAmount",    "Action",  "xsd:decimal", False, "has bet amount",        "Bet amount."),
        ("hasPotSize",      "Pot",     "xsd:decimal", False, "has pot size",          "Pot size."),
        ("isBlind",         "Player",  "xsd:boolean", False, "is blind",              "Indicates if the player is in a blind position."),
        ("isAllIn",         "Player",  "xsd:boolean", False, "is all-in",             "Indicates if the player went all-in."),
        ("isFolded",        "Player",  "xsd:boolean", False, "is folded",             "Indicates if the player folded."),
        ("playerName",      "Player",  "xsd:string",  False, "player name",           "Player's name."),
        ("seatNumber",      "Player",  "xsd:integer", True,  "seat number",           "Seat number (1-10)."),
        ("tableSize",       "Table",   "xsd:integer", True,  "table size",            "Number of seats at the table."),
        ("gameId",          "Game",    "xsd:string",  True,  "game ID",               "Unique game identifier."),
        ("handNumber",      "Game",    "xsd:integer", False, "hand number",           "Hand number in the session."),
        ("hasDealerButton", "Player",  "xsd:boolean", True,  "has dealer button",     "Indicates if the player has the dealer button."),
        ("isHeadsUp",       "Game",    "xsd:boolean", True,  "is heads-up",           "Indicates if the game is heads-up (2 players)."),
        ("potSequence",     "SidePot", "xsd:integer", True,  "pot sequence",          "Side pot order."),
    ]

    for name, domain, rng, func, lbl, cmt in data_props:
        fstr = " , owl:FunctionalProperty" if func else ""
        w(f"poker:{name} a owl:DatatypeProperty{fstr} ;")
        w(f"    rdfs:domain poker:{domain} ;")
        w(f"    rdfs:range {rng} ;")
        w(f'    rdfs:label "{lbl}" ;')
        w(f'    rdfs:comment "{cmt}" .')
        blank()

    # ================================================================
    # MODULE 11 – Structural Axioms
    # ================================================================
    section("MODULE 11: Structural Axioms and Restrictions")

    w("# Global axioms that guarantee the consistency of the ontology.")
    blank()
    comment("Hand Ranking Disjunction (9 base classes, RoyalFlush excluded)")
    w("[] a owl:AllDisjointClasses ;")
    w("    owl:members ( poker:HighCard poker:OnePair poker:TwoPair poker:ThreeOfAKind")
    w("                  poker:Straight poker:Flush poker:FullHouse poker:FourOfAKind")
    w("                  poker:StraightFlush ) .")
    blank()

    comment("Round Disjunction (a round cannot be two types at once)")
    w("[] a owl:AllDisjointClasses ;")
    w("    owl:members ( poker:PreFlop poker:FlopRound poker:TurnRound poker:RiverRound poker:Showdown ) .")
    blank()

    comment("Base Action Disjunction (AllIn omitted: it is a composite class)")
    w("[] a owl:AllDisjointClasses ;")
    w("    owl:members ( poker:Fold poker:Check poker:Call poker:Bet poker:Raise ) .")
    blank()

    comment("PostBlind is distinct from all voluntary actions")
    for act in ["Fold", "Check", "Call", "Bet", "Raise"]:
        w(f"poker:PostBlind owl:disjointWith poker:{act} .")
    blank()

    comment("Betting Structure Disjunction")
    w("[] a owl:AllDisjointClasses ;")
    w("    owl:members ( poker:NoLimitHoldEm poker:LimitHoldEm poker:PotLimitHoldEm ) .")
    blank()

    comment("Community Cards Disjunction")
    w("[] a owl:AllDisjointClasses ;")
    w("    owl:members ( poker:Flop poker:Turn poker:River ) .")
    blank()

    comment("MainPot disjoint with SidePot")
    w("poker:MainPot owl:disjointWith poker:SidePot .")
    blank()

    comment("Position Disjunctions (compatible with 2-player heads-up)")
    comment("BigBlindPosition is ALWAYS exclusive with all others")
    comment("ButtonPosition is NOT disjoint with SmallBlindPosition (they coincide in heads-up)")
    for pos in ["SmallBlindPosition", "ButtonPosition", "EarlyPosition",
                "MiddlePosition", "LatePosition"]:
        w(f"poker:BigBlindPosition owl:disjointWith poker:{pos} .")
    blank()

    comment("Intermediate positions are mutually exclusive in 3+ player games")
    w("poker:EarlyPosition owl:disjointWith poker:MiddlePosition .")
    w("poker:EarlyPosition owl:disjointWith poker:LatePosition .")
    w("poker:MiddlePosition owl:disjointWith poker:LatePosition .")

    # ================================================================
    # MODULE 12 – Individuals (ABox)
    # ================================================================
    section("MODULE 12: Individuals (ABox)")

    w("# The ABox defines the concrete individuals of the domain.")
    w("# Total: 88 individuals")
    w("#   4  suits (Suit)                  — closed by owl:oneOf in TBox")
    w("#   13 ranks (Rank)                  — Ace with dual value: 14 (high) and 1 (low)")
    w("#   52 cards (Card)                  — 13 ranks × 4 suits")
    w("#   6  positions (Position)")
    w("#   3  betting structures (BettingStructure)")
    w("#   10 hand rankings (HandRanking)   — including RoyalFlush")
    blank()
    # ── Suits ──
    comment("Suits (4 individuals)")
    for s in SUITS:
        w(f"poker:{s} a poker:Suit ;")
        w(f'    rdfs:label "{s}" .')
    blank()

    # ── Ranks ──
    w("# The Ace also has hasRankValueLow=1 for the low straight (A-2-3-4-5).")
    comment("Ranks (13 individuals)")
    for r in RANKS:
        v = RANK_VALUES[r]
        w(f"poker:{r} a poker:Rank ;")
        w(f"    poker:hasRankValue {v} ;")
        if r == "Ace":
            w(f"    poker:hasRankValueLow 1 ;")
        w(f'    rdfs:label "{r}" .')
    blank()

    # ── 52 Cards ──
    comment("Cards (52 individuals)")
    for s in SUITS:
        for r in RANKS:
            w(f"{ciri(r, s)} a poker:Card ;")
            w(f"    poker:hasSuit poker:{s} ;")
            w(f"    poker:hasRank poker:{r} ;")
            w(f'    rdfs:label "{clabel(r, s)}" .')
        blank()

    # ── Positions ──
    comment("Positions (6 individuals)")
    pos_inds = [
        ("SmallBlind", "SmallBlindPosition", "Small Blind"),
        ("BigBlind",   "BigBlindPosition",   "Big Blind"),
        ("UTG",        "EarlyPosition",      "Under the Gun"),
        ("MiddlePos",  "MiddlePosition",     "Middle Position"),
        ("CutOff",     "LatePosition",       "Cutoff"),
        ("Button",     "ButtonPosition",     "Button"),
    ]
    for ind, cls, label in pos_inds:
        w(f"poker:{ind} a poker:{cls} ;")
        w(f'    rdfs:label "{label}" .')
    blank()

    # ── BettingStructure ──
    comment("Betting Structures (3 individuals)")
    for ind, cls, label in [("NLHE", "NoLimitHoldEm",  "No Limit Texas Hold'em"),
                             ("LHE",  "LimitHoldEm",    "Limit Texas Hold'em"),
                             ("PLHE", "PotLimitHoldEm", "Pot Limit Texas Hold'em")]:
        w(f"poker:{ind} a poker:{cls} ;")
        w(f'    rdfs:label "{label}" .')
    blank()

    # ── HandRanking individuals ──
    comment("Hand Rankings (10 individuals)")
    hr_inds = [
        ("HighCardRanking",      "HighCard",      "High Card Ranking"),
        ("OnePairRanking",       "OnePair",       "One Pair Ranking"),
        ("TwoPairRanking",       "TwoPair",       "Two Pair Ranking"),
        ("ThreeOfAKindRanking",  "ThreeOfAKind",  "Three of a Kind Ranking"),
        ("StraightRanking",      "Straight",      "Straight Ranking"),
        ("FlushRanking",         "Flush",         "Flush Ranking"),
        ("FullHouseRanking",     "FullHouse",     "Full House Ranking"),
        ("FourOfAKindRanking",   "FourOfAKind",   "Four of a Kind Ranking"),
        ("StraightFlushRanking", "StraightFlush", "Straight Flush Ranking"),
        ("RoyalFlushRanking",    "RoyalFlush",    "Royal Flush Ranking"),
    ]
    for ind, cls, label in hr_inds:
        w(f"poker:{ind} a poker:{cls} ;")
        w(f'    rdfs:label "{label}" .')
    blank()

    comment("beats chain: 9 direct relations, 36 pairs inferred by transitivity")
    beats = [
        ("RoyalFlushRanking",    "StraightFlushRanking"),
        ("StraightFlushRanking", "FourOfAKindRanking"),
        ("FourOfAKindRanking",   "FullHouseRanking"),
        ("FullHouseRanking",     "FlushRanking"),
        ("FlushRanking",         "StraightRanking"),
        ("StraightRanking",      "ThreeOfAKindRanking"),
        ("ThreeOfAKindRanking",  "TwoPairRanking"),
        ("TwoPairRanking",       "OnePairRanking"),
        ("OnePairRanking",       "HighCardRanking"),
    ]
    for a, b in beats:
        w(f"poker:{a} poker:beats poker:{b} .")
    blank()

    # ── AllDifferent ──
    comment("AllDifferent Axioms")
    blank()

    comment("4 distinct suits")
    w("[] a owl:AllDifferent ;")
    w("    owl:distinctMembers ( poker:Spades poker:Hearts poker:Diamonds poker:Clubs ) .")
    blank()

    comment("13 distinct ranks")
    w("[] a owl:AllDifferent ;")
    w(f"    owl:distinctMembers ( {' '.join('poker:' + r for r in RANKS)} ) .")
    blank()

    comment("52 distinct cards")
    all_cards = [ciri(r, s) for s in SUITS for r in RANKS]
    w("[] a owl:AllDifferent ;")
    w("    owl:distinctMembers (")
    for i in range(0, len(all_cards), 4):
        chunk = " ".join(all_cards[i:i + 4])
        w(f"        {chunk}")
    w("    ) .")
    blank()

    comment("6 distinct positions")
    w("[] a owl:AllDifferent ;")
    w(f"    owl:distinctMembers ( {' '.join('poker:' + p[0] for p in pos_inds)} ) .")
    blank()

    comment("10 distinct rankings")
    w("[] a owl:AllDifferent ;")
    w(f"    owl:distinctMembers ( {' '.join('poker:' + h[0] for h in hr_inds)} ) .")
    blank()

    comment("3 distinct betting structures")
    w("[] a owl:AllDifferent ;")
    w("    owl:distinctMembers ( poker:NLHE poker:LHE poker:PLHE ) .")

    # ================================================================
    # MODULE 13 – Hand Inference Layer
    # ================================================================
    section("MODULE 13: Hand Inference Layer")

    w("# This module defines owl:equivalentClass patterns that allow an OWL 2 DL")
    w("# reasoner (HermiT/Pellet/FaCT++) to automatically classify poker hands.")
    w("# REQUIREMENT: the 5 cards of the BestHand must be explicitly assigned")
    w("# with containsCard for the reasoner to activate classification.")
    w("#")
    w("# Module contents:")
    w("#   13.1  4  suit helper classes        (SpadesCard, HeartsCard, ...)")
    w("#   13.2  13 rank helper classes         (TwoRankCard, AceRankCard, ...)")
    w("#   13.3  10 BestHand-by-ranking classes (OnePairBestHand, FlushBestHand, ...)")
    w("#   13.4  Royal Flush by cards           (4  variants: one per suit)")
    w("#   13.5  Steel Wheel by cards           (4  variants: one per suit)")
    w("#   13.6  Standard Straight Flush        (32 variants: 8 ranges × 4 suits)")
    w("#   13.7  Four of a Kind by cards        (13 variants: one per rank)")
    w("#   13.8  Full House by cards             (156 variants: 13 trips × 12 pairs)")
    w("#   13.9  Flush by cards                  (4  variants: one per suit)")
    w("#   13.10 Straight by ranks               (10 variants)")
    w("#   13.11 Three of a Kind by cards        (13 variants)")
    w("#   13.12 Two Pair by cards               (78 variants: C(13,2))")
    w("#   13.13 One Pair by cards               (13 variants)")
    w("#   13.14 High Card by complement         (1  class, requires closed world)")
    blank()

    # ----------------------------------------------------------------
    # 13.1 Suit Helper Classes
    # ----------------------------------------------------------------
    comment("13.1 Suit Helper Classes (4 classes)")
    w("# XxxCard ≡ Card ∩ hasSuit.{Xxx}")
    w("# Enable owl:qualifiedCardinality over cards of a specific suit.")
    w("# Example: =5 containsCard SpadesCard detects a Spades Flush.")
    blank()
    for suit in SUITS:
        w(f"poker:{suit}Card a owl:Class ;")
        w( "    owl:equivalentClass [")
        w( "        a owl:Class ;")
        w( "        owl:intersectionOf (")
        w( "            poker:Card")
        w(f"            [ a owl:Restriction ; owl:onProperty poker:hasSuit ; owl:hasValue poker:{suit} ]")
        w( "        )")
        w( "    ] ;")
        w(f'    rdfs:label "{suit} Card" ;')
        w(f'    rdfs:comment "Card whose suit is {suit}." .')
        blank()

    # ----------------------------------------------------------------
    # 13.2 Rank Helper Classes
    # ----------------------------------------------------------------
    comment("13.2 Rank Helper Classes (13 classes)")
    w("# XxxRankCard ≡ Card ∩ hasRank.{Xxx}")
    w("# Enable owl:qualifiedCardinality over cards of a specific rank.")
    w("# Example: >=3 containsCard AceRankCard detects Three of a Kind (Aces).")
    blank()
    for rank in RANKS:
        w(f"poker:{rank}RankCard a owl:Class ;")
        w( "    owl:equivalentClass [")
        w( "        a owl:Class ;")
        w( "        owl:intersectionOf (")
        w( "            poker:Card")
        w(f"            [ a owl:Restriction ; owl:onProperty poker:hasRank ; owl:hasValue poker:{rank} ]")
        w( "        )")
        w( "    ] ;")
        w(f'    rdfs:label "{rank} Rank Card" ;')
        w(f'    rdfs:comment "Card whose rank is {rank}." .')
        blank()

    # ----------------------------------------------------------------
    # 13.3 BestHand by Ranking (10 classes)
    # ----------------------------------------------------------------
    comment("13.3 BestHand by Ranking (10 defined classes)")
    w("# XxxBestHand ≡ BestHand ∩ hasHandRanking.{XxxRanking}")
    w("# Classify a BestHand already tagged with its ranking individual.")
    blank()
    bh_by_ranking = [
        ("HighCard",      "HighCardRanking",      "High Card",        "BestHand classified as High Card."),
        ("OnePair",       "OnePairRanking",       "One Pair",         "BestHand classified as One Pair."),
        ("TwoPair",       "TwoPairRanking",       "Two Pair",         "BestHand classified as Two Pair."),
        ("ThreeOfAKind",  "ThreeOfAKindRanking",  "Three of a Kind",  "BestHand classified as Three of a Kind."),
        ("Straight",      "StraightRanking",      "Straight",         "BestHand classified as Straight."),
        ("Flush",         "FlushRanking",         "Flush",            "BestHand classified as Flush."),
        ("FullHouse",     "FullHouseRanking",     "Full House",       "BestHand classified as Full House."),
        ("FourOfAKind",   "FourOfAKindRanking",   "Four of a Kind",   "BestHand classified as Four of a Kind."),
        ("StraightFlush", "StraightFlushRanking", "Straight Flush",   "BestHand classified as Straight Flush."),
        ("RoyalFlush",    "RoyalFlushRanking",    "Royal Flush",      "BestHand classified as Royal Flush."),
    ]
    for hand_type, ranking_ind, label, cmt in bh_by_ranking:
        cls = f"{hand_type}BestHand"
        w(f"poker:{cls} a owl:Class ;")
        w( "    owl:equivalentClass [")
        w( "        a owl:Class ;")
        w( "        owl:intersectionOf (")
        w( "            poker:BestHand")
        w(f"            [ a owl:Restriction ; owl:onProperty poker:hasHandRanking ; owl:hasValue poker:{ranking_ind} ]")
        w( "        )")
        w( "    ] ;")
        w(f'    rdfs:label "Best Hand: {label}" ;')
        w(f'    rdfs:comment "{cmt}" .')
        blank()

    # ----------------------------------------------------------------
    # 13.4 Royal Flush by cards (4 variants)
    # ----------------------------------------------------------------
    comment("13.4 Royal Flush by Cards Pattern (4 variants)")
    w("# RoyalFlushByCardsBestHand ≡ BestHand ∩ unionOf(")
    w("#   [10-J-Q-K-A of Spades] ⊔ [10-J-Q-K-A of Hearts] ⊔ ...)")
    w("# A reasoner automatically detects the Royal Flush by cards.")
    blank()
    royal_ranks = ["Ten", "Jack", "Queen", "King", "Ace"]
    royal_members = []
    for suit in SUITS:
        member = [hv_card_r(f"{rank}Of{suit}") for rank in royal_ranks]
        royal_members.append(member)
    write_m13_union_equiv(
        "RoyalFlushByCardsBestHand",
        royal_members,
        "Royal Flush by Cards",
        "BestHand with 10-J-Q-K-A of the same suit (4 possible variants, one per suit)."
    )

    # ----------------------------------------------------------------
    # 13.5 Steel Wheel by cards (4 variants)
    # ----------------------------------------------------------------
    comment("13.5 Steel Wheel by Cards Pattern (4 variants)")
    w("# SteelWheelBestHand: A-2-3-4-5 of the same suit.")
    w("# The lowest Straight Flush; the Ace counts as 1.")
    blank()
    wheel_ranks = ["Ace", "Two", "Three", "Four", "Five"]
    steel_wheel_members = []
    for suit in SUITS:
        member = [hv_card_r(f"{rank}Of{suit}") for rank in wheel_ranks]
        steel_wheel_members.append(member)
    write_m13_union_equiv(
        "SteelWheelBestHand",
        steel_wheel_members,
        "Steel Wheel by Cards",
        "BestHand with A-2-3-4-5 of the same suit (low straight flush, 4 variants)."
    )

    # ----------------------------------------------------------------
    # 13.6 Standard Straight Flush (32 variants)
    # ----------------------------------------------------------------
    comment("13.6 Standard Straight Flush by Cards Pattern (32 variants)")
    w("# StraightFlushByCardsBestHand: 8 intermediate ranges × 4 suits = 32 variants.")
    w("# Excludes Royal Flush (Broadway × 4) and Steel Wheel (Wheel × 4),")
    w("# modeled as separate classes in 13.4 and 13.5.")
    blank()
    std_sf_members = []
    for straight_indices in STRAIGHTS[1:9]:   # indices 1-8: excludes Wheel (0) and Broadway (9)
        straight_ranks = [RANKS[i] for i in straight_indices]
        for suit in SUITS:
            member = [hv_card_r(f"{rank}Of{suit}") for rank in straight_ranks]
            std_sf_members.append(member)
    write_m13_union_equiv(
        "StraightFlushByCardsBestHand",
        std_sf_members,
        "Straight Flush by Cards",
        "BestHand with standard straight flush (8 ranges x 4 suits = 32 variants). Excludes Royal Flush and Steel Wheel."
    )

    # ----------------------------------------------------------------
    # 13.7 Four of a Kind (13 variants)
    # ----------------------------------------------------------------
    comment("13.7 Four of a Kind by Cards Pattern (13 variants)")
    w("# FourOfAKindByCardsBestHand: qualifiedCardinality 4 for each rank.")
    blank()
    four_members = [qc_rank_r(rank, 4) for rank in RANKS]
    write_m13_union_equiv(
        "FourOfAKindByCardsBestHand",
        four_members,
        "Four of a Kind by Cards",
        "BestHand with exactly 4 cards of the same rank (13 possible variants, one per rank)."
    )

    # ----------------------------------------------------------------
    # 13.8 Full House (156 variants)
    # ----------------------------------------------------------------
    comment("13.8 Full House by Cards Pattern (156 variants)")
    w("# FullHouseByCardsBestHand: 13 ranks for trips × 12 ranks for pair.")
    w("# LARGE AXIOM: 156 members in the unionOf — correct in OWL 2 DL.")
    w("# Each member: (=3 XRankCard ∩ =2 YRankCard) with X ≠ Y.")
    blank()
    fh_members = []
    for trio_rank in RANKS:
        for pair_rank in RANKS:
            if trio_rank != pair_rank:
                fh_members.append([
                    qc_rank_r(trio_rank, 3),
                    qc_rank_r(pair_rank, 2)
                ])
    write_m13_union_equiv(
        "FullHouseByCardsBestHand",
        fh_members,
        "Full House by Cards",
        "BestHand with trips and a pair of different ranks (156 variants = 13 x 12)."
    )

    # ----------------------------------------------------------------
    # 13.9 Flush (4 variants)
    # ----------------------------------------------------------------
    comment("13.9 Flush by Cards Pattern (4 variants)")
    w("# FlushByCardsBestHand: qualifiedCardinality 5 for each suit class.")
    w("# Note: includes Straight Flush and Royal Flush as special cases.")
    w("# Fine distinction is made via hasHandRanking.")
    blank()
    flush_members = [qc_suit_r(suit, 5) for suit in SUITS]
    write_m13_union_equiv(
        "FlushByCardsBestHand",
        flush_members,
        "Flush by Cards",
        "BestHand with 5 cards of the same suit (4 variants). Semantic superclass of Straight Flush."
    )

    # ----------------------------------------------------------------
    # 13.10 Straight by Ranks (10 variants)
    # ----------------------------------------------------------------
    comment("13.10 Straight by Ranks Pattern (10 variants)")
    w("# StraightByRanksBestHand: minQualifiedCardinality 1 for each required rank.")
    w("# Note: includes Straight Flush and Royal Flush. Distinction via hasHandRanking.")
    blank()
    straight_members = []
    for straight_indices in STRAIGHTS:
        straight_ranks = [RANKS[i] for i in straight_indices]
        member = [qc_rank_r(rank, 1, "minQualifiedCardinality") for rank in straight_ranks]
        straight_members.append(member)
    write_m13_union_equiv(
        "StraightByRanksBestHand",
        straight_members,
        "Straight by Ranks",
        "BestHand with 5 consecutive ranks (10 variants: wheel to broadway). Semantic superclass of Straight Flush."
    )

    # ----------------------------------------------------------------
    # 13.11 Three of a Kind by cards (13 variants)
    # ----------------------------------------------------------------
    comment("13.11 Three of a Kind by Cards Pattern (13 variants)")
    w("# ThreeOfAKindByCardsBestHand: minQualifiedCardinality 3 for each rank.")
    w("# Note: also detects Full House (has trips) and Four of a Kind (4 >= 3).")
    blank()
    toak_members = [qc_rank_r(rank, 3, "minQualifiedCardinality") for rank in RANKS]
    write_m13_union_equiv(
        "ThreeOfAKindByCardsBestHand",
        toak_members,
        "Three of a Kind by Cards",
        "BestHand with at least 3 cards of the same rank (13 variants). Includes Full House and Four of a Kind."
    )

    # ----------------------------------------------------------------
    # 13.12 Two Pair by cards (78 variants)
    # ----------------------------------------------------------------
    comment("13.12 Two Pair by Cards Pattern (78 variants)")
    w("# TwoPairByCardsBestHand: C(13,2) = 78 combinations of 2 distinct ranks.")
    w("# Each member: (>=2 XRankCard ∩ >=2 YRankCard) with X < Y (lexicographic order).")
    w("# Note: also detects Full House (the trips have >=2 of that rank).")
    blank()
    tp_members = []
    for i, rank1 in enumerate(RANKS):
        for rank2 in RANKS[i + 1:]:
            tp_members.append([
                qc_rank_r(rank1, 2, "minQualifiedCardinality"),
                qc_rank_r(rank2, 2, "minQualifiedCardinality")
            ])
    write_m13_union_equiv(
        "TwoPairByCardsBestHand",
        tp_members,
        "Two Pair by Cards",
        "BestHand with at least 2 cards of two distinct ranks (78 variants = C(13,2)). Includes Full House."
    )

    # ----------------------------------------------------------------
    # 13.13 One Pair by cards (13 variants)
    # ----------------------------------------------------------------
    comment("13.13 One Pair by Cards Pattern (13 variants)")
    w("# OnePairByCardsBestHand: minQualifiedCardinality 2 for each rank.")
    w("# This is the broadest condition: also covers Two Pair, Three of a Kind,")
    w("# Full House, and Four of a Kind (all have at least one pair).")
    blank()
    op_members = [qc_rank_r(rank, 2, "minQualifiedCardinality") for rank in RANKS]
    write_m13_union_equiv(
        "OnePairByCardsBestHand",
        op_members,
        "One Pair by Cards",
        "BestHand with at least 2 cards of the same rank (13 variants). Includes Two Pair, Three of a Kind, Full House, Four of a Kind."
    )

    # ----------------------------------------------------------------
    # 13.14 High Card by complement
    # ----------------------------------------------------------------
    comment("13.14 High Card by Complement Pattern")
    w("# HighCardByCardsBestHand ≡ BestHand")
    w("#   ∩ ¬OnePairByCardsBestHand     (no pair of any rank)")
    w("#   ∩ ¬StraightByRanksBestHand   (no 5 ranks of any straight)")
    w("#   ∩ ¬FlushByCardsBestHand      (no 5 cards of the same suit)")
    w("# WARNING: requires closed world (all cards assigned).")
    w("# In a benchmark with complete ABox this pattern works correctly.")
    blank()
    w("poker:HighCardByCardsBestHand a owl:Class ;")
    w( "    owl:equivalentClass [")
    w( "        a owl:Class ;")
    w( "        owl:intersectionOf (")
    w( "            poker:BestHand")
    w( "            [ a owl:Class ; owl:complementOf poker:OnePairByCardsBestHand ]")
    w( "            [ a owl:Class ; owl:complementOf poker:StraightByRanksBestHand ]")
    w( "            [ a owl:Class ; owl:complementOf poker:FlushByCardsBestHand ]")
    w( "        )")
    w( "    ] ;")
    w( '    rdfs:label "High Card by Complement" ;')
    w( '    rdfs:comment "BestHand with no pair, straight, or flush (requires closed world over assigned cards)." .')
    blank()

    w("# ============================================================")
    w("# MODULE 13 COMPLETE")
    w("# ─────────────────────────────────────────────────────────────")
    w("# Helper classes:              17  (4 suit + 13 rank)")
    w("# BestHand by ranking:         10")
    w("# Inference patterns:")
    w("#   Royal Flush:               4  variants")
    w("#   Steel Wheel:               4  variants")
    w("#   Standard Straight Flush:  32  variants")
    w("#   Four of a Kind:           13  variants")
    w("#   Full House:              156  variants")
    w("#   Flush:                     4  variants")
    w("#   Straight:                 10  variants")
    w("#   Three of a Kind:          13  variants")
    w("#   Two Pair:                 78  variants")
    w("#   One Pair:                 13  variants")
    w("#   High Card:                 1  class (complement)")
    w("# ─────────────────────────────────────────────────────────────")
    w("# Total inference variants: 328")
    w("# ============================================================")

    # ── WRITE FILE ──
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        f.write("\n")

    print(f"✓ Complete ontology written to {OUTPUT}")
    print(f"  Total lines: {len(lines)}")
    print(f"  Cards generated: {sum(1 for s in SUITS for _ in RANKS)}")
    print(f"  M13 helper classes: {len(SUITS)} suit + {len(RANKS)} rank = {len(SUITS)+len(RANKS)}")
    print(f"  Full House variants: {len([1 for t in RANKS for p in RANKS if t != p])}")
    print(f"  Two Pair variants: {len(RANKS)*(len(RANKS)-1)//2}")


if __name__ == "__main__":
    generate()
