import pytest
from deck import Suits, Card, Deck, StandardDeck


@pytest.mark.parametrize("suit,value,expected", [
    (Suits.SPADES, "A", "Ace of spades"),
    (Suits.HEARTS, "K", "King of hearts"),
    (Suits.DIAMONDS, "2", "Two of diamonds"),
    (Suits.CLUBS, "10", "Ten of clubs"),
])
def test_card(suit, value, expected):
    card = Card(suit, value)
    assert card.long_name == expected


def test_standard_deck_creation():
    # a new standard deck
    assert type(StandardDeck()[0]) == Card
    assert len(StandardDeck()) == 52


def test_deck_creation():
    # an empty deck
    deck = Deck()
    assert len(deck) == 0
    deck = Deck([])
    assert len(deck) == 0

    # deck from list
    cards = [Card(Suits.SPADES, "A"), Card(Suits.CLUBS, "A")]
    deck = Deck(cards)
    assert len(deck) == 2
    assert deck[0] == cards[0]

    # deck from generator
    deck = Deck(card for card in cards)
    assert len(deck) == 2
    assert deck[0] == cards[0]


def test_deck_shuffle():
    assert len(StandardDeck().shuffle()) == 52
    empty_deck = Deck()
    empty_deck.shuffle()
    assert len(empty_deck) == 0


def test_deck_take():
    deck = StandardDeck()
    taken = deck.take(12)
    # taking cards should return correct number of cards,
    # and shorten the original deck
    assert len(taken) == 12
    assert len(deck) == 40
    # taking no cards should return empty deck
    taken = deck.take(0)
    assert len(taken) == 0
    assert len(deck) == 40
    # trying to take more cards than there are should only take len(deck) cards
    taken = deck.take(50)
    assert len(taken) == 40
    assert len(deck) == 0


def test_deck_take_negative():
    deck = StandardDeck()
    with pytest.raises(ValueError):
        deck.take(-5)


def test_deck_add():
    ace_of_spades = Card(Suits.SPADES, "A")
    ace_of_hearts = Card(Suits.HEARTS, "A")
    deck = Deck([])
    assert len(deck) == 0
    deck.append(ace_of_spades)
    assert len(deck) == 1
    assert deck[0] == ace_of_spades
    deck.append(ace_of_hearts)
    assert len(deck) == 2
    assert deck[1] == ace_of_hearts


def test_deck_to_string():
    deck = Deck()
    assert str(deck) == "Deck()"
    ace_of_spades = Card(Suits.SPADES, "A")
    ten_of_hearts = Card(Suits.HEARTS, "10")
    deck = Deck([ace_of_spades, ten_of_hearts])
    assert str(deck) == "Deck(♠A, ♥10)"


def test_numeric_values():
    two = Card(Suits.SPADES, "2")
    ten = Card(Suits.SPADES, "10")
    jack = Card(Suits.SPADES, "J")
    queen = Card(Suits.SPADES, "Q")
    king = Card(Suits.SPADES, "K")
    ace = Card(Suits.SPADES, "A")
    assert int(two) == 2
    assert int(ten) == 10
    assert int(jack) == 11
    assert int(queen) == 12
    assert int(king) == 13
    assert int(ace) == 14
