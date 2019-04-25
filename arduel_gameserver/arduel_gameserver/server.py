import argparse
import socket
import threading
import time
import select


gameState = {"users" : {},"shots":{},
             "position":{}, "forward":{}
}


def get_amount_of_health(response):
    if "head" in response:
        return 5
    if "body" in response:
        return 2
    if "arm" in response:
        return 1
    return 0


def get_direction_of_dodge(response):

    if "left" in response:
        print("left")
        return -1
    if "right" in response:
        print("right")
        return 1
    return 0


def get_direction_of_fowrward(response):
    try:
        num = float(response.split(" ")[-1])

    except Exception as e:
        print(str(e))
        return 0
    return num


class ThreadedServer(object):
    #saved_variable = "hallo"



    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.lock = threading.Lock() # for synchronizing the threads

    def listen(self):
        global gameState
        self.sock.listen(120)
        while True:
            client, address = self.sock.accept()
            client.settimeout(200)
            threading.Thread(target = self.listenToClient,args = (client,address)).start()

    def listenToClient(self, client, address):
        size = 1024
        t = time.process_time()
        while True:
            try:
                if self.isready(address): # game begins
                    while(len(gameState["users"])!=2):
                        time.sleep(0.05)
                    client.send(str.encode(str(gameState)+ "\n")) # to get the avatars
                    print("sent go to user "+ str(address))
                    for i in range(3):
                        client.send(str.encode("countdown :" +str(3-i) + "\n"))
                        time.sleep(1)
                    client.send(str.encode("GO\n"))
                    game_running=True
                    otherPlayer = self.get_other_player(address[1])
                    currentState= "no_state"
                    while(game_running):
                        client.setblocking(0)

                        data2=False
                        ready = select.select([client], [], [], 1)
                        if ready[0]: #if current player is ready
                            data2 = client.recv(4096)
                            t = time.process_time()
                        if data2: #data was received
                            response = data2.decode().strip()
                            print(response)

                            if "shot" in response:
                                minus_health =0

                                minus_health = get_amount_of_health(response)
                                gameState["shots"][otherPlayer]-= minus_health
                                client.send(str.encode("registered :" + response + "\n"))

                            elif "dodge" in response:
                                direction = get_direction_of_dodge(response)
                                gameState["position"][address[1]]+= direction
                                if abs(gameState["position"][address[1]])>3:
                                    gameState["position"][address[1]] -= direction
                                client.send(str.encode("registered :" + response + "\n"))

                            elif "forward" in response:
                                direction = get_direction_of_fowrward(response)
                                gameState["forward"][address[1]]= direction
                                client.send(str.encode("registered :" + response + "\n"))
                        # shot = gameState["shots"][otherPlayer].get(False)
                        # print(currentState)
                        #elapsed_time = time.process_time() - t
                     #   print(str(elapsed_time))
                        if currentState != str(gameState):
                            if gameState["shots"][address[1]] <= 0:
                                #we lost
                                client.send(str.encode("RESULT: lost\n"))
                                client.send(str.encode("goodbye\n"))
                            elif gameState["shots"][otherPlayer] <= 0:
                                #we won
                                client.send(str.encode("RESULT: won \n"))
                                client.send(str.encode("goodbye\n"))

                            client.send(str.encode(str(gameState)+"\n"))

                            currentState = str(gameState)





                data = client.recv(size)
                if data:
                    # Set the response to echo back the recieved data
                    response = data.decode().strip()
                    print(response)

                    if("ready" in response):
                        avatar = '1'
                        if(len(response.split(' '))>1):
                            avatar = response.split(' ')[1]
                        self.ready(address,avatar)
                        print(gameState)
                        client.send(b"you're ready, waiting for others\n")
                        id_text = "your id : "+ str(address[1])+"\n"
                        client.send(str.encode(id_text))

                        gameState["shots"][address[1]] = 100
                        gameState["position"][address[1]] = 0
                        gameState["forward"][address[1]]=0
                    # client.send(b"Connection working")
                    else:
                        client.send(str.encode(str(gameState)+"\n"))

                # elif data == "quit":
                else:
                    raise error('Client disconnected')

            except Exception as e:
                print(str(e))
                client.close()
                self.unready(address)
                return False

    def get_other_player(self,me):
        for user in gameState["users"]:
            if user!= me:
                return user


    def unready(self,address):
        with self.lock:
            gameState["users"][address[1]] = False

    def ready(self,address,avatar):
        with self.lock:
            gameState["users"][address[1]] = avatar

    def isready(self,address):
        return gameState["users"].__contains__(address[1])

parser = argparse.ArgumentParser(description='run a game server')
parser.add_argument('--port', '-p', const=8881, default=8881, nargs='?',
                    help='the port of the server')

args = parser.parse_args()

if __name__ == "__main__":
    port_num = int(args.port)
    print("Started server on port: " + str(port_num))
    ThreadedServer('',port_num).listen()