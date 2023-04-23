import eventlet
import socketio
from random import randint
import json
import os
sio = socketio.Server()
app = socketio.WSGIApp(sio)


# recieve and store scores from client
player_scores = [0, 0]
# To client tradition/addition mode
game_mode = 0
# To client if both 0 , game end,display score
player_status = [1, 1]

# To client indicate game start
game_status = 0
i = 0
j= 0
k=0

gap_size = 2
row_start = 3

@sio.event
def connect(sid, environ):
    global i
    i = i+1
    print('connection established (server)', sid)
    print("ip"+environ['REMOTE_ADDR'])
    
    if (i == 2):
        #print("starting to send data")
        sio.emit('recieve_connection', {})
        os.system('clear')    
        
        '''
        #prompt user to choose game mode
        print("Two player connected to the server.")
        print("Choose game mode: ")
        print("1. Traditional Mode")
        print("2. Additional Mode")
        choice = 1
        #while 1:
        #    if(choice == 1 or choice == 2):
        choice = input("Your choice")
        #        break
        game_mode = int(choice)
        '''

        sio.start_background_task(send_data)
        i=0

@sio.event
def recieve_mode():
    pass
    
@sio.event
def send_data():
    global gap_size, row_start, game_mode
    #print(game_mode)
    gap_size = randint(2, 4)
    row_start = randint(1 + gap_size, 6)

    #print("game_mode = " + str(game_mode))
    # send when game start
    if game_status == 0:
        sio.emit('recieve_msg', {"gap_size": gap_size,
                                 "row_start": row_start,
                                 "game_mode": game_mode,
                                 "game_status": 0})         # 0 means havn't lose

row_start_arr = []
gap_size_arr = []
for a in range(1, 100):
    gap_size_arr.append(randint(2, 4))
    row_start_arr.append(randint(1 + gap_size_arr[a-1], 6))

@sio.event
def recieve_msg(self, recdata):
    global player_scores, player_status,gap_size,row_start,j,k,game_mode
    # recieve when player1 or player2 lose or request column
    jsondata = json.loads(json.dumps(recdata))
        #print(j)
    if (jsondata['player'] == 1):
        #print("player1 lose")
        player_scores[0] = jsondata['score']
        player_status[0] = 0
    elif (jsondata['player'] == 2):
        player_scores[1] = jsondata['score']
        player_status[1] = 0
        #print("player2 lose")

    # response to request column
    elif (jsondata['player'] == 3):
        #print(j)
        j=j+1
        sio.emit('recieve_msg', {"gap_size": gap_size_arr[j],
                                 "row_start": row_start_arr[j],
                                 "game_status": game_status,
                                 "game_mode": game_mode})
    elif (jsondata['player'] ==4):
        #print(j)
        k=j+1
        sio.emit('recieve_msg', {"gap_size": gap_size_arr[k],
                                 "row_start": row_start_arr[k],
                                 "game_status": game_status,
                                 "game_mode": game_mode})
    elif (jsondata['player']==5):
        #print("received gamemode from client, send it to all clients again")
        game_mode=jsondata['game_mode']
        print("game_mode = " + str(game_mode))
        sio.emit('recieve_msg',{"gap_size": gap_size,
                                 "row_start": row_start,
                                 "game_status": 1,
                                 "game_mode": game_mode})

    #print(player_status)
    # print final result when game end
    # print(str(player_status[0]) + ", " + str(player_status[1]))
    if player_status[0] == 0 and player_status[1] == 0:
        print("player 1 : player 2")
        string = ""
        if (player_scores[0] > player_scores[1]):
            print(str(player_scores[0])+"  : "+str(player_scores[1]))
            print("player 1 win")
            string = "|    player 1 wins    |"
        elif (player_scores[0] == player_scores[1]):
            print(str(player_scores[0])+":"+str(player_scores[1]))
            print("Draw")
            string = "|        Draw         |"
        elif (player_scores[0] < player_scores[1]):
            print(str(player_scores[0])+":"+str(player_scores[1]))
            print("player 2 win")
            string = "|    player 2 wins    |"

        # send result to clients
        result = "|        " + str(player_scores[0]) + "  : "+str(player_scores[1]) + "       |" + "\n" + string
        sio.emit('recieve_result', {"result": result})
    else:
        pass
        #print(recdata)


@sio.event
def disconnect(sid):
    print('disconnected from server', sid)


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
    print("main")
