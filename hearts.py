import random

from deck import Deck
from deck import StandardDeck
from deck import Suits


CARD_VALUES = {card_val: value for value, card_val in enumerate(StandardDeck.CARD_VALUES)}


class Player:
    """
    Base class for Hearts players
    Classes inheriting from this should implement
    play_card method that chooses which card to play
    """

    def __init__(self, name):
        self.name = name
        self.cards = Deck()
        self.collected_cards = Deck()
        self.points = []

    def has_two_of_clubs(self):
        return any(card.long_name == "Two of clubs" for card in self.cards)

    def has_suit(self, suit):
        return any(card.suit == suit for card in self.cards)

    def give_points(self, points):
        self.points.append(points)

    def play_card(self, hand):
        pass
        if len(hand) > 0:
            required = hand[0].suit
            if not self.has_suit(required):
                required = None
        else:
            required = None
        print(f"{self.name}'s cards:", *[f"({i}){str(card)}" for i, card in enumerate(self.cards)])
        while True:
            to_play = input("Pick a card: ")
            i = int(to_play)
            print(f"You picked {self.cards[i]}")
            if required and self.cards[i].suit != required:
                print(f"You must play {required}. Try again.")
                continue
            break
        return self.cards.pop(i)

    @property
    def total_points(self):
        return sum(self.points)


class HumanPlayerCLI(Player):
    def play_card(self, hand):
        if len(hand) > 0:
            required = hand[0].suit
            if not self.has_suit(required):
                required = None
        else:
            required = None
        print(f"{self.name}'s cards:", *[f"({i}){str(card)}" for i, card in enumerate(self.cards)])
        while True:
            to_play = input("Pick a card: ")
            i = int(to_play)
            print(f"You picked {self.cards[i]}")
            if required and self.cards[i].suit != required:
                print(f"You must play {required}. Try again.")
                continue
            break
        return self.cards.pop(i)


class RNGPlayer(Player):
    def play_card(self, hand):
        if len(hand) > 0:
            required = hand[0].suit
            if not self.has_suit(required):
                required = None
        else:
            required = None
        # print(f"{self.name}'s cards:", *map(str, self.cards))
        while True:
            i = random.randrange(len(self.cards))
            if required and self.cards[i].suit != required:
                continue
            break
        print(f"{self.name} plays {self.cards[i]}")
        return self.cards.pop(i)


class HeartsGame:
    def __init__(self, players, point_limit=100):
        if len(players) != 4:
            raise ValueError("only 4 player games are supported right now")
        self.players = players
        self.point_limit = 100
        self.deck = StandardDeck()

    @classmethod
    def score(cls, deck):
        score = 0
        for card in deck:
            if card.suit == Suits.HEARTS:
                score += 1
            elif card.long_name == "Queen of spades":
                score += 13
        return score

    def is_game_over(self):
        return any(player.total_points >= self.point_limit for player in self.players)

    def play(self):
        while not self.is_game_over():
            self.play_round()

    def play_round(self):
        self.deck = StandardDeck().shuffle()
        CARDS_PER_PLAYER = 13
        for player in self.players:
            player.collected_cards = Deck()
            player_cards = self.deck.take(CARDS_PER_PLAYER)
            player_cards.sort(key=lambda card: ("♣♦♠♥".index(card.suit.value), int(card)))
            player.cards = player_cards

        # rotate players until the first player has two of clubs
        while not self.players[0].has_two_of_clubs():
            self.players.append(self.players.pop(0))

        # TODO: exchanging cards
        # TODO: enforce first player playing two of clubs
        # TODO: enforce hearts being disallowed until opened

        for hand_number in range(1, CARDS_PER_PLAYER + 1):
            print(f"Hand {hand_number}:")
            hand = Deck()
            for player in self.players:
                played_card = player.play_card(hand)
                hand.append(played_card)

            # "winner" collects cards
            winner_index = self.winner_index(hand)
            winner = self.players[winner_index]
            print(f"{winner.name} takes the hand")
            winner.collected_cards.extend(hand)
            # rotate players so the winner of this hand begins the next round
            self.players = self.players[winner_index:] + self.players[:winner_index]

        # TODO: implement shoot the moon
        print("Round over")
        for player in self.players:
            num_cards = len(player.collected_cards)
            score = HeartsGame.score(player.collected_cards)
            print(f"Player {player.name} collected {num_cards} cards and scored {score}")
            player.give_points(score)

    def player_scores(self):
        return {player.name: player.points for player in self.players}

    def scoresheet(self):
        scores = self.player_scores()
        game_over = self.is_game_over()
        COL_WIDTH = 11
        scoresheet = []
        if game_over:
            scoresheet.append("FINAL SCORES:")
        else:
            scoresheet.append("CURRENT SCORES:")
        scoresheet.append("=" * (4 * COL_WIDTH + 3 * 3))
        scoresheet.append(" | ".join(f"{player:^{COL_WIDTH}}" for player in scores))
        for round_scores in zip(*scores.values()):
            scoresheet.append(" | ".join(f"{score:^{COL_WIDTH}}" for score in round_scores))
        if game_over:
            scoresheet.append("-|-".join(["-"*11]*4))
            scoresheet.append(" | ".join(f"{sum(scores):^{COL_WIDTH}}" for scores in scores.values()))
        return "\n".join(scoresheet)

    def winner_index(self, hand):
        cards_played = enumerate(hand)
        winner_index, max_card = next(cards_played)
        for (i, card) in cards_played:
            if card.suit == max_card.suit and int(card) > int(max_card):
                max_card = card
                winner_index = i
        return winner_index


if __name__ == "__main__":
    players = [
        # HumanPlayerCLI("Alice"),
        RNGPlayer("Alice"),
        RNGPlayer("Bob"),
        RNGPlayer("Cleo"),
        RNGPlayer("Dimitri")
    ]
    hearts_game = HeartsGame(players)
    hearts_game.play()
    print(hearts_game.scoresheet())
