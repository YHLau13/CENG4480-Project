from time import sleep
import sense_hat
import socketio
import json
import os

sio = socketio.Client()


sense = sense_hat.SenseHat()
sense.clear()

col_color = (0, 255, 0)
bird = 2
lives = 3
pipes = [(7, 3, 3)]


game_over = False
setup = True
lift = False


# socketio global variable
player_scores = [0, 0]
game_mode = 1
player_status = [1, 1]
game_status = 0


sense.set_pixel(0, 0, col_color)
col_color = sense.get_pixel(0, 0)
sense.set_pixel(0, 0, (255, 0, 0))
sense.clear()


def move_pipes():
    global pipes
    # Shift x coordinate of colums to left
    pipes = [(c[0] - 1, c[1], c[2]) for c in pipes]

    # Add a new column if needed
    if max([c[0] for c in pipes]) == 4:
        send_msg()
        pipes.append((7, row_start, gap_size))


def draw_column(col, custom_color=None):

    if custom_color:
        back_color = custom_color
    else:
        back_color = (0, 0, 0)

    # Construct a list of column color and background color tuples, then set those pixels
    x, gap_start, gap_size = col
    c = [col_color] * 8
    c[gap_start - gap_size: gap_start] = [back_color] * gap_size
    for y, color in enumerate(c):
        sense.set_pixel(x, y, color)


def draw_screen(custom_color=None):
    back_color = (0, 0, 0)
    if custom_color:
        back_color = custom_color
    sense.clear(back_color)
    # Filter out offscreen pipes then draw visible pipes
    visible_cols = [c for c in pipes if c[0] >= 0]
    for c in visible_cols:
        draw_column(c, back_color)


def draw_bird():

    global bird, lives, game_over

    sense.set_pixel(3, bird, sense.get_pixel(3, bird))

    if game_mode == 1:
        bird += 1

    if bird > 7:
        bird = 7
    if bird < 0:
        bird = 0

    # Collisions are when the bird moves onto a column
    hit = sense.get_pixel(3, bird) == col_color
    if hit:
        flash_screen()
        lives -= 1

    for i in range(lives):
        sense.set_pixel(0, i, (200, 200, 200))

    game_over = lives < 0

    sense.set_pixel(3, bird, (255, 0, 0))


def flash_screen():
    draw_screen((255, 255, 255))
    sleep(.2)
    sense.set_pixel(3, bird, (255, 0, 0))
    sleep(.1)
    draw_screen()


def startgame():
    global col_color, bird, lives, pipes,  game_over, lift
    # print("startgame(): game_mode = " + str(game_mode)
    draw_screen()
    draw_bird()

    while True:

        move_pipes()
        draw_screen()
        draw_bird()
        sleep(0.8)

        if (game_mode == 1):
            for event in sense.stick.get_events()[::-1]:
                if event.action == 'pressed':
                    if event.direction == 'up':
                        move_pipes()
                        draw_screen()
                        draw_bird()
                        lift = True
                else:
                    lift = False
        elif (game_mode == 2):
            roll = sense.get_orientation()["roll"]

            if 20 < roll < 159 and bird < 7:
                bird = bird + 1
                draw_screen()
                draw_bird()
            elif 339 > roll > 160 and bird > 0:
                bird = bird - 1
                draw_screen()
                draw_bird()

        if game_over:
            send_msg()
            sense.show_message(str(len(pipes) - 2) + "pts")
            break


@sio.event
def connect():
    os.system('clear')
    print('connection established (player 1)')

# recieve when game start
# recieve response when game end:score


def send_game_mode():
    print("1. Traditional Mode")
    print("2. Additional Mode")
    game_mode = input("Choose Game Mode:")
    # print("send_game_mode(): game_mode = " + str(game_mode))
    sio.emit('recieve_msg', {'player': 5, "game_mode": game_mode})


@sio.event
def recieve_msg(recdata):
    # print(recdata)
    global gap_size, row_start, player_status, player_scores, game_mode, game_status
    # recieve when game start or recieve column during game
    jsondata = json.loads(json.dumps(recdata))
    gap_size = jsondata['gap_size']
    row_start = jsondata['row_start']

    game_mode = int(jsondata['game_mode'])

    # recieve when game start
    if (jsondata['game_status'] == 1 and game_status == 0):
        # print("game mode before startgame(): " + str(game_mode))
        startgame()
        game_status = 1
    if (jsondata['game_status'] == 0 and jsondata['game_mode'] == 0):
        sio.start_background_task(send_game_mode)

@sio.event
def send_msg():
    # send when a player lose
    if (game_over):
        sio.emit('recieve_msg', {'player':  2, 'score': len(pipes) - 2})
    # send when request column
    if (not game_over):
        sio.emit('recieve_msg', {'player':  4})


@sio.event
def recieve_result(recdata):

    # recieve when game over
    jsondata = json.loads(json.dumps(recdata))
    print("\n")
    print("-----------------------")
    print("|    Match Result     |")
    print("-----------------------")
    print("| player 2 : player 1 |")
    print(jsondata['result'])
    print("-----------------------")


@sio.event
def disconnect():
    print('disconnected from client2')


sio.connect("http://:5000")     # enter the ip of your hosting device
