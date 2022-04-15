import random
import enum
import collections


class Suits(enum.Enum):
    HEARTS = "♥"
    SPADES = "♠"
    DIAMONDS = "♦"
    CLUBS = "♣"

    def __str__(self):
        return self.value


class Card():
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value

    def __repr__(self):
        return f'Card(suit={self.suit.name}, value="{self.value}")'

    def __str__(self):
        return f"{self.suit}{self.value}"

    def __int__(self):
        return StandardDeck.CARD_NUMERIC_VALUES[self.value]

    @property
    def long_name(self):
        """Returns the name of the card in human-readable form."""
        value_name = StandardDeck.CARD_VALUE_NAMES.get(self.value, self.value)
        return f"{value_name} of {self.suit.name}".capitalize()


class Deck(collections.UserList):
    def __init__(self, seq=None):
        if seq is None:
            self.data = []
        else:
            self.data = [x for x in seq]

    def __str__(self):
        return f'Deck({", ".join(str(card) for card in self.data)})'

    def shuffle(self):
        """Randomizes the order of cards in the deck."""
        random.shuffle(self.data)
        return self

    def take(self, n=1):
        """
        Removes n last cards from this deck.
        Returns a new deck with the removed cards.
        May return fewer than n cards if the deck runs out.
        Raises ValueError if n is negative.
        """
        if n < 0:
            raise ValueError(f"Number of cards to take must be positive (tried to take {n})")
        return Deck(self.pop() for _ in range(n) if len(self) > 0)


class StandardDeck(Deck):
    """A deck that initially contains the 52 cards found in a standard deck of playing cards"""
    CARD_VALUES = "2 3 4 5 6 7 8 9 10 J Q K A".split()
    CARD_NAMES = "two three four five six seven eight nine ten jack queen king ace".split()
    CARD_VALUE_NAMES = {k: v for k, v in zip(CARD_VALUES, CARD_NAMES)}
    CARD_NUMERIC_VALUES = {card_value: i for i, card_value in enumerate(CARD_VALUES, 2)}

    def __init__(self):
        self.data = [Card(suit, value) for suit in Suits for value in StandardDeck.CARD_VALUES]
