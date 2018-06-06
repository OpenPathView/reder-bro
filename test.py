import zmq
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:8551")
socket.setsockopt_string(zmq.SUBSCRIBE, "")
print(socket.recv())
