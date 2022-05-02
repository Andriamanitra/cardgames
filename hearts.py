import random
from collections.abc import Iterator

from deck import Card
from deck import Deck
from deck import StandardDeck
from deck import Suits
from utils import NotOk
from utils import Ok
from utils import Result


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

    def has(self, card_name: str) -> bool:
        return any(card.long_name == card_name for card in self.cards)

    def has_suit(self, suit: Suits):
        return any(card.suit == suit for card in self.cards)

    def give_points(self, points: int):
        self.points.append(points)

    def choose_action(self, trick: Deck, legal_moves: list[Card]) -> Card:
        raise NotImplementedError("choose_action method not implemented for Player class")

    def reset(self):
        """
        This method is called every time a new game starts.
        Can be used to prepare a player object for a fresh round.
        """
        self.collected_cards = Deck()
        self.points = []

    @property
    def total_points(self) -> int:
        return sum(self.points)


class HumanPlayerCLI(Player):
    def choose_action(self, trick, legal_moves):
        print(f"{self.name}'s cards:", *[f"({i}){str(card)}" for i, card in enumerate(self.cards)])
        while True:
            to_play = input("Pick a card: ")
            try:
                i = int(to_play)
                chosen_card = self.cards[i]
                break
            except (ValueError, IndexError):
                print("Invalid choice, try again")
        print(f"You picked {chosen_card}")
        return chosen_card


class RNGPlayer(Player):
    def choose_action(self, trick, legal_moves):
        chosen_card = random.choice(legal_moves)
        print(f"{self.name} plays {chosen_card}")
        return chosen_card


class HeartsGame:
    def __init__(self, players: list[Player], point_limit: int = 100):
        if len(players) != 4:
            raise ValueError("only 4 player games are supported right now")
        self.CARDS_PER_PLAYER = 13
        self.MAX_POINTS_PER_ROUND = 26
        self.players = players
        self._current_player_idx = 0
        self.game_over = False
        self.point_limit = point_limit
        self.hearts_opened = False
        self.deck = StandardDeck()
        self.trick = Deck()
        self.trick_number = 1
        self.trick_finished = False
        self.last_trick = None
        self.last_trick_winner = None
        self.last_starter_idx = 0

    @staticmethod
    def score_deck(deck: Deck) -> int:
        score = 0
        for card in deck:
            if card.suit == Suits.HEARTS:
                score += 1
            elif card.long_name == "Queen of spades":
                score += 13
        return score

    @property
    def current_player(self) -> Player:
        return self.players[self._current_player_idx]

    def __iter__(self) -> Iterator[tuple[Player, Deck]]:
        while not self.game_over:
            yield self.current_player, self.trick

    def start(self):
        """
        Sets up a fresh game. Must be called before playing cards with `play_card()`.
        """
        for player in self.players:
            player.reset()
        self._initialize_round()
        return self

    def legal_moves(self, cards: Deck) -> list[Card]:
        """
        Returns a list of cards in the given deck that could be legally played
        in the current state of the game.
        """
        return [card for card in cards if self.check_move(card)]

    def check_move(self, card: Card) -> Result:
        """
        Returns a truthy Result if the card can be legally played in the
        current state of the game.
        Otherwise returns a falsey Result with a reason.
        """
        player = self.current_player
        if card not in player.cards:
            return NotOk("The current player does not own that card!")
        if len(self.trick) == 0:
            if self.trick_number == 1 and card.long_name != "Two of clubs":
                return NotOk("A round must start with the two of clubs!")
            if not self.hearts_opened and card.suit == Suits.HEARTS:
                if any(card.suit != Suits.HEARTS for card in player.cards):
                    return NotOk("Hearts can't be played before they are opened!")
        else:
            required = self.trick[0].suit
            if card.suit != required and player.has_suit(required):
                return NotOk("The play must follow suit!")
        return Ok()

    def play_card(self, card: Card) -> Result:
        """
        Advances game state if the played card was a valid move.
        Returns true if the play finished a trick.
        """
        self.trick_finished = False
        check_result = self.check_move(card)
        if not check_result.is_ok:
            return check_result

        self.current_player.cards.remove(card)
        self.trick.append(card)
        self._current_player_idx += 1
        self._current_player_idx %= len(self.players)

        if len(self.trick) == len(self.players):
            self._finish_trick()
        return Ok()

    def player_scores(self) -> dict[str, list[int]]:
        return {player.name: player.points for player in self.players}

    def scoresheet(self) -> str:
        scores = self.player_scores()
        COL_WIDTH = 11
        scoresheet = []
        if self.game_over:
            scoresheet.append("FINAL SCORES:")
        else:
            scoresheet.append("CURRENT SCORES:")
        scoresheet.append("=" * (4 * COL_WIDTH + 3 * 3))
        scoresheet.append(" | ".join(f"{player:^{COL_WIDTH}}" for player in scores))
        for round_scores in zip(*scores.values()):
            scoresheet.append(" | ".join(f"{score:^{COL_WIDTH}}" for score in round_scores))
        if self.game_over:
            scoresheet.append("-|-".join(["-" * 11] * 4))
            scoresheet.append(" | ".join(f"{sum(scores):^{COL_WIDTH}}" for scores in scores.values()))
        return "\n".join(scoresheet)

    def _initialize_round(self):
        self.deck = StandardDeck().shuffle()
        for player in self.players:
            player.collected_cards = Deck()
            player_cards = self.deck.take(self.CARDS_PER_PLAYER)
            player_cards.sort(key=lambda card: ("♣♦♠♥".index(card.suit.value), int(card)))
            player.cards = player_cards

        # the player who has two of clubs starts
        for i, player in enumerate(self.players):
            if player.has("Two of clubs"):
                self._current_player_idx = i
                break

        self.trick_number = 1
        self.hearts_opened = False
        self.trick = Deck()

    def _finish_trick(self):
        self.trick_finished = True
        if not self.hearts_opened and any(card.suit == Suits.HEARTS for card in self.trick):
            self.hearts_opened = True

        # "winner" collects cards and begins the next trick
        cards_played = enumerate(self.trick)
        winner_index, max_card = next(cards_played)
        for (i, card) in cards_played:
            if card.suit == max_card.suit and int(card) > int(max_card):
                max_card = card
                winner_index = i
        self.last_trick = self.trick
        self.last_starter_idx = self._current_player_idx
        winning_player_index = (self.last_starter_idx + winner_index) % len(self.players)
        self.last_trick_winner = self.players[winning_player_index]
        self._current_player_idx = winning_player_index

        winner = self.current_player
        print(f"{winner.name} takes the trick")
        winner.collected_cards.extend(self.trick)
        self.trick_number += 1
        self.trick = Deck()
        if self.trick_number > self.CARDS_PER_PLAYER:
            self._finish_round()

    def _finish_round(self):
        print("\nRound over! Results:")
        shot_the_moon = None
        # check for shoot the moon before distributing points regularly
        for player in self.players:
            if self.score_deck(player.collected_cards) == self.MAX_POINTS_PER_ROUND:
                shot_the_moon = player
                break

        if shot_the_moon is not None:
            print(f"Player {shot_the_moon.name} shoots the moon!")
            print(f"All other players get {self.MAX_POINTS_PER_ROUND} added to their score.")
            for player in self.players:
                player.give_points(0 if shot_the_moon is player else self.MAX_POINTS_PER_ROUND)
        else:
            for player in self.players:
                num_cards = len(player.collected_cards)
                score = self.score_deck(player.collected_cards)
                print(f"Player {player.name} collected {num_cards} cards and scored {score}")
                player.give_points(score)

        if any(player.total_points >= self.point_limit for player in self.players):
            self.game_over = True
        else:
            self._initialize_round()


if __name__ == "__main__":
    players: list[Player] = [
        # HumanPlayerCLI("Alice"),
        RNGPlayer("Alice"),
        RNGPlayer("Bob"),
        RNGPlayer("Cleo"),
        RNGPlayer("Dimitri")
    ]

    game = HeartsGame(players).start()
    for current_player, trick in game:
        legal_moves = game.legal_moves(current_player.cards)
        chosen_card = current_player.choose_action(trick, legal_moves)
        play_result = game.play_card(chosen_card)
        if not play_result.is_ok:
            print(play_result.reason, "Try again.")

    print()
    print(game.scoresheet())
