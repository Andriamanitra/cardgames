import random

from deck import Card
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

    def __init__(self, name: str):
        self.name = name
        self.cards = Deck()
        self.collected_cards = Deck()
        self.points: list[int] = []

    def has_two_of_clubs(self) -> bool:
        return any(card.long_name == "Two of clubs" for card in self.cards)

    def give_points(self, points: int):
        self.points.append(points)

    def play_card(self, trick: Deck, legal_moves: list[Card]) -> Card:
        raise NotImplementedError("play_card method not implemented for Player class")

    @property
    def total_points(self):
        return sum(self.points)


class HumanPlayerCLI(Player):
    def play_card(self, trick: Deck, legal_moves: list[Card]) -> Card:
        print(f"{self.name}'s cards:", *[f"({i}){str(card)}" for i, card in enumerate(self.cards)])
        while True:
            to_play = input("Pick a card: ")
            i = int(to_play)
            print(f"You picked {self.cards[i]}")
            if self.cards[i] not in legal_moves:
                if len(legal_moves) == 1:
                    print(f"Illegal move. You must play {legal_moves[0]}.")
                elif len(trick) == 0:
                    print("Hearts have not been opened yet! Try again.")
                else:
                    print("You must follow suit. Try again.")
                continue
            break
        return self.cards.pop(i)


class RNGPlayer(Player):
    def play_card(self, trick: Deck, legal_moves: list[Card]) -> Card:
        chosen_card = random.choice(legal_moves)
        self.cards.remove(chosen_card)
        print(f"{self.name} plays {chosen_card}")
        return chosen_card


class HeartsGame:
    def __init__(self, players: list[Player], point_limit: int = 100):
        if len(players) != 4:
            raise ValueError("only 4 player games are supported right now")
        self.CARDS_PER_PLAYER = 13
        self.players = players
        self.point_limit = point_limit
        self.hearts_opened = False
        self.deck = StandardDeck()

    @classmethod
    def score(cls, deck: Deck) -> int:
        score = 0
        for card in deck:
            if card.suit == Suits.HEARTS:
                score += 1
            elif card.long_name == "Queen of spades":
                score += 13
        return score

    def is_game_over(self) -> bool:
        return any(player.total_points >= self.point_limit for player in self.players)

    def legal_moves(self, trick: Deck, cards: list[Card]) -> list[Card]:
        if len(cards) == self.CARDS_PER_PLAYER and len(trick) == 0:
            # first move, forced to play 2 of clubs
            return [card for card in cards if card.long_name == "Two of clubs"]

        if len(trick) == 0:
            # first card in a trick, can play anything except
            # hearts if they are not yet opened
            playable = [card for card in cards if self.hearts_opened or card.suit != Suits.HEARTS]
        else:
            # must follow suit
            required = trick[0].suit
            playable = [card for card in cards if card.suit == required]

        # if it's impossible to follow suit (or not play hearts),
        # then a player is free to play any card
        return playable if playable else list(cards)

    def play(self):
        while not self.is_game_over():
            self.play_round()

    def play_round(self):
        self.deck = StandardDeck().shuffle()
        self.hearts_opened = False
        for player in self.players:
            player.collected_cards = Deck()
            player_cards = self.deck.take(self.CARDS_PER_PLAYER)
            player_cards.sort(key=lambda card: ("♣♦♠♥".index(card.suit.value), int(card)))
            player.cards = player_cards

        # rotate players until the first player has two of clubs
        while not self.players[0].has_two_of_clubs():
            self.players.append(self.players.pop(0))

        # TODO: exchanging cards

        for trick_number in range(1, self.CARDS_PER_PLAYER + 1):
            print(f"============ Trick #{trick_number} ============")
            trick = Deck()
            for player in self.players:
                legal_moves = self.legal_moves(trick, player.cards)
                played_card = player.play_card(trick, legal_moves)
                if played_card not in legal_moves:
                    raise ValueError(f"Illegal move ({played_card}) was played")
                trick.append(played_card)

            if not self.hearts_opened and any(card.suit == Suits.HEARTS for card in trick):
                self.hearts_opened = True

            # "winner" collects cards
            winner_index = self.winner_index(trick)
            winner = self.players[winner_index]
            print(f"{winner.name} takes the trick")
            winner.collected_cards.extend(trick)
            # rotate players so the winner of this trick begins the next trick
            self.players = self.players[winner_index:] + self.players[:winner_index]

        print("\nRound over! Results:")
        # check for shoot the moon before distributing points regularly
        for player in self.players:
            if HeartsGame.score(player.collected_cards) == 26:
                print(f"Player {player.name} shoots the moon!")
                print("All other players get 26 added to their score.")
                for other_player in self.players:
                    if other_player is player:
                        player.give_points(0)
                    else:
                        other_player.give_points(26)
                return

        for player in self.players:
            num_cards = len(player.collected_cards)
            score = HeartsGame.score(player.collected_cards)
            print(f"Player {player.name} collected {num_cards} cards and scored {score}")
            player.give_points(score)

    def player_scores(self) -> dict[str, list[int]]:
        return {player.name: player.points for player in self.players}

    def scoresheet(self) -> str:
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
            scoresheet.append("-|-".join(["-" * 11] * 4))
            scoresheet.append(" | ".join(f"{sum(scores):^{COL_WIDTH}}" for scores in scores.values()))
        return "\n".join(scoresheet)

    def winner_index(self, trick: Deck) -> int:
        cards_played = enumerate(trick)
        winner_index, max_card = next(cards_played)
        for (i, card) in cards_played:
            if card.suit == max_card.suit and int(card) > int(max_card):
                max_card = card
                winner_index = i
        return winner_index


if __name__ == "__main__":
    players: list[Player] = [
        # HumanPlayerCLI("Alice"),
        RNGPlayer("Alice"),
        RNGPlayer("Bob"),
        RNGPlayer("Cleo"),
        RNGPlayer("Dimitri")
    ]
    hearts_game = HeartsGame(players)
    hearts_game.play()
    print()
    print(hearts_game.scoresheet())
