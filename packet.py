#packet.py

SEQ = 0
ACK_NUM = 1
FLAG = 2
DATA = 3

FLAG_SYN = 0b001
FLAG_ACK = 0b010
FLAG_FIN = 0b100


def new_packet(seq, ack_num, syn, ack_bit, fin, data):
	flag = 0b000
	if syn:
		flag = flag | FLAG_SYN
	if ack_bit:
		flag = flag | FLAG_ACK
	if fin:
		flag = flag | FLAG_FIN
	packet = [seq, ack_num, flag, data]
	return packet

def is_syn(packet):
	boo = packet[FLAG] & FLAG_SYN
	return (boo == FLAG_SYN)

def is_fin(packet):
	boo = packet[FLAG] & FLAG_FIN
	return (boo == FLAG_FIN)

def is_ack(packet):
	boo = packet[FLAG] & FLAG_ACK
	return (boo == FLAG_ACK)

def get_data(packet):
	return packet[DATA]

def get_ack(packet):
	return packet[ACK_NUM]

def get_seq(packet):
	return packet[SEQ]