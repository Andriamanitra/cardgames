import asyncio
import json
import logging

from sanic import Sanic

from hearts import HeartsGame
from hearts import Player
from hearts import RNGPlayer
from utils import NotOk
from utils import Ok
from utils import Result

logging.basicConfig(
    format="[%(levelname)s] [%(asctime)s] %(message)s",
    datefmt="%Y-%d-%m %H:%M:%S %z",
    level=logging.INFO
)
app = Sanic("SanicHeartsGame")


class InvalidMoveException(Exception):
    pass


class NoMoveChosenException(Exception):
    pass


class WebSocketPlayer(Player):
    def __init__(self, name: str, ws):
        super().__init__(name)
        self.ws = ws
        self.selection = None

    async def info(self, text):
        msg = json.dumps({"msg_type": "INFO", "text": text})
        await self.send(msg)

    async def tell_cards(self):
        msg = message("YOUR_CARDS", cards=[card.to_object() for card in self.cards])
        await self.send(msg)

    async def send(self, msg):
        if self.ws is not None:
            await self.ws.send(msg)

    def choose_action(self, trick, legal_moves):
        if self.selection is None:
            raise NoMoveChosenException
        try:
            return self.cards[int(self.selection)]
        except (ValueError, IndexError):
            logging.debug(f"Invalid card selection ({self.selection})")
            raise InvalidMoveException(f"Invalid card selection ({self.selection})")
        finally:
            self.selection = None


class GameRoom:
    def __init__(self, room_id):
        self.room_id = room_id
        self.members = {}
        self.human_players = {}
        self.game = None
        self.host_name = None
        self.host = None

    @property
    def started(self):
        return self.game is not None

    async def add_member(self, name, ws) -> Result:
        if name in self.members:
            return NotOk("Name already taken")
        if len(name) < 3 or len(name) > 24:
            return NotOk("Name needs to be at least 3 and at most 24 characters long")
        if len(self.members) < 1:
            self.host_name = name
            self.host = ws
            await ws.send(message("HOST"))
        self.members[name] = ws
        await ws.send(self.msg_state())
        await self.broadcast_users()
        return Ok()

    async def disconnect_member(self, name):
        self.members.pop(name)
        if name in self.human_players:
            self.human_players[name].ws = None
        await self.broadcast_users()

    def msg_state(self) -> str:
        """Generate a message about the gameroom state"""
        if self.game and self.game.game_over:
            return message("GAME_STATE", status="GAME_OVER")
        if self.game:
            return message(
                "GAME_STATE",
                status="GAME_IN_PROGRESS",
                playing=self.game.current_player.name,
                trick=[card.to_object() for card in self.game.trick]
            )
        return message("GAME_STATE", status="WAITING_FOR_HOST")

    def msg_users(self) -> str:
        """Generate a message about the users in the gameroom"""
        users = list(self.members)
        players = [] if not self.started else [player.name for player in self.game.players]
        return message("USERS", users=users, players=players, host=self.host_name)

    async def broadcast_state(self):
        """Inform all members about the state of the gameroom"""
        msg = self.msg_state()
        await self.broadcast(msg)

    async def broadcast_users(self):
        """Inform all members about users in the room"""
        msg = self.msg_users()
        await self.broadcast(msg)

    async def broadcast(self, msg):
        """Send a message to all members in the gameroom (including non-players)"""
        for ws in self.members.values():
            await ws.send(msg)

    def start_game(self):
        players = []
        for name, ws in self.members.items():
            player = WebSocketPlayer(name, ws)
            self.human_players[name] = player
            players.append(player)
            if len(players) == 4:
                break
        rng_player_idx = 1
        while len(players) < 4:
            rng_player = RNGPlayer(f"RNGPlayer{rng_player_idx}")
            players.append(rng_player)
            rng_player_idx += 1
        self.game = HeartsGame(players).start()

    async def play(self):
        for current_player, trick in self.game:
            legal_moves = self.game.legal_moves(current_player.cards)
            try:
                chosen_card = current_player.choose_action(trick, legal_moves)
            except NoMoveChosenException:
                return
            except InvalidMoveException as exc:
                await current_player.info(str(exc))
                return
            play_result = self.game.play_card(chosen_card)
            if not play_result.is_ok:
                await current_player.info(play_result.reason)
                return
            if self.game.trick_finished:
                trick_winner = self.game.last_trick_winner.name
                msg = message(
                    "TRICK_FINISH",
                    trick=[card.to_object() for card in self.game.last_trick],
                    winner=trick_winner,
                    last_starter_idx=self.game.last_starter_idx
                )
                await self.broadcast(msg)
                if self.game.trick_number == 1:
                    scores = self.game.player_scores()
                    await self.broadcast(message("SCORES", scores=scores))

            await self.broadcast_state()


def message(msg_type, **kwargs):
    kwargs["msg_type"] = msg_type
    return json.dumps(kwargs)


def infomsg(msg):
    return message("INFO", text=msg)


async def handle_ws_message(gameroom, username, ws, recvd):
    try:
        msg_obj = json.loads(recvd)
    except json.JSONDecodeError:
        await ws.send(infomsg("invalid message"))
        return
    logging.debug(f"received {msg_obj=}")
    match(gameroom.started, msg_obj):
        case(False, {"msg_type": "START"}):
            if ws is gameroom.host:
                gameroom.start_game()
                scores = gameroom.game.player_scores()
                await gameroom.broadcast(infomsg("Game started!"))
                await gameroom.broadcast(message("SCORES", scores=scores))
                for player in gameroom.human_players.values():
                    await player.tell_cards()
                await gameroom.play()
                await gameroom.broadcast_state()
                await gameroom.broadcast_users()
        case(True, {"msg_type": "PLAY", "card_index": i}):
            try:
                player = gameroom.human_players[username]
            except KeyError:
                return
            player.selection = i
            if gameroom.game.current_player is not player:
                await player.info("It's not your turn!")
                return
            await gameroom.play()
            await player.tell_cards()
            state_message = gameroom.msg_state()
            await gameroom.broadcast(state_message)
        case(_, {"msg_type": "CHAT", "message": chatmessage}):
            msg = message("CHAT", sender=username, message=chatmessage)
            await gameroom.broadcast(msg)
        case _:
            print(f"Invalid message {msg_obj=}")


def _generate_id(starting_id):
    current_id = starting_id

    def inner():
        nonlocal current_id
        current_id += 1
        return f"{current_id:05x}"
    return inner


def _generate_name(starting_id):
    current_id = starting_id

    def inner():
        nonlocal current_id
        current_id += 1
        return f"~anon{current_id:03}"
    return inner


generate_id = _generate_id(789988)
generate_name = _generate_name(0)


@app.websocket("/game")
async def game(request, ws):
    args = request.get_args()
    room_id = args.get("rid") or generate_id()
    name = args.get("name") or generate_name()

    if room_id not in rooms:
        rooms[room_id] = GameRoom(room_id)
        logging.info(f"[{room_id}] GameRoom created")

    gameroom = rooms[room_id]
    # TODO: if there is disconnected player with same name steal their spot
    result = await gameroom.add_member(name, ws)
    if not result.is_ok:
        await ws.send(infomsg(f"Unable to join game room ({result.reason})"))
        await ws.close()
        return

    await ws.send(infomsg(f"Connected to game room {room_id}"))
    logging.info(f"[{room_id}] {name} connected")

    try:
        while True:
            recvd = await ws.recv()
            await handle_ws_message(gameroom, name, ws, recvd)
    except asyncio.exceptions.CancelledError:
        # websocket connection closed or lost
        await gameroom.disconnect_member(name)
        logging.info(f"[{room_id}] {name} disconnected")
        if not gameroom.members:
            rooms.pop(room_id)
            logging.info(f"[{room_id}] GameRoom deleted")
        elif name == gameroom.host_name:
            gameroom.host_name, gameroom.host = next(iter(gameroom.members.items()))
            await gameroom.host.send(message("HOST"))
            logging.info(f"[{room_id}] {gameroom.host_name} is the new host")


rooms: dict[str, GameRoom] = {}

if __name__ == "__main__":
    app.run(debug=False)
