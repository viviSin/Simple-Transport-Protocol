#Receiver.py

import socket,sys
from packet import *
from random import randint

STATE_IDLE = 0
STATE_WELCOME = 1
STATE_FINISH = 2

state = STATE_IDLE


def main():
	global state
	global tot_data 
	# global tot_segment 
	# global tot_dup_ack 
	# if (len(sys.argv) != 3):
	# 	 sys.exit("invalidate input")

	tot_data = 0
	tot_segment = 0
	tot_dup_ack = 0

	receiver_host        = "localhost"
	receiver_port        = int(sys.argv[1])
	filename             = str(sys.argv[2])
	
	
	# receiver_host        = "localhost"
	# receiver_port        = 7239
	# filename    = "hiii.txt"

	receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	receiver.bind((receiver_host, receiver_port))
	#for buffering
	window = []
	ack_rec = 0
	first_packet_arrived = False
	stop = False
	yseq = randint(1,9)
	sender_host = 0
	sender_port = 0
	
	file = open(filename,'w')
	file.close()
	


	log = open('Receiver_log.txt','w')
	log.close()
	log = open('Receiver_log.txt','a')

	while True:
		if stop:
			p3 = new_packet(yseq, 0,False, False, True,"")
			receiver.sendto(str(p3), (sender_host, sender_port))
			stop= False
			continue
		data, sender = receiver.recvfrom(receiver_port)
		p = eval(data)
		sender_host = sender[0]
		sender_port = sender[1]

		if (is_fin(p)):
			if(is_ack and int(get_ack(p)) == int(yseq)+1):
				state == STATE_FINISH
				t1 = 'Amount of data received: '+str(tot_data)+' bytes\n'
				t2 = 'Number of data segmentes received: '+str(tot_segment)+'\n'
				t3 = 'Number of duplicate segments received: '+str(tot_dup_ack)+'\n'
				log.write(t1)
				log.write(t2)
				log.write(t3)
				log.close()
				sys.exit()
			else:
				ack_a = int(get_seq(p))+1
				stop = True
				p2 = new_packet(0, str(ack_a),False, True, True,"")
				receiver.sendto(str(p2), (sender_host, sender_port))
				continue
		elif (state == STATE_IDLE):
			tot_data = 0
			tot_segment = 0
			tot_dup_ack = 0
			if (is_syn(p)):
				#seq, ack_num, syn, ack_bit, fin, data
				ack_a=int(get_seq(p))+1
				state = STATE_WELCOME
				p2 = new_packet(str(yseq), str(ack_a),True, True, False,"")
				receiver.sendto(str(p2), (sender_host, sender_port))
		elif (state == STATE_WELCOME):
			if (not is_ack(p)):
				tot_segment += 1
				if (int(get_seq(p)) == 0 and not first_packet_arrived):
					#first 
					first_packet_arrived = True
					ack_rec = int(get_seq(p))+int(len(get_data(p)))
					write_to_file(filename, str(get_data(p)))
				elif  (ack_rec == int(get_seq(p)) and first_packet_arrived):
					#new ack
					if (not window):
						ack_rec = int(get_seq(p))+int(len(get_data(p)))
						write_to_file(filename, str(get_data(p)))
					else:
						tot_dup_ack+=1
						write_to_file(filename, str(get_data(p)))
						ack_rec =int(get_seq(p))+int(len(get_data(p)))
						for z in window:
							if (int(ack_rec) == int(get_seq(z))):
								write_to_file(filename, str(get_data(z)))
								ack_rec = int(get_seq(z))+int(len(get_data(z)))
						window[:] = [value for value in window if int(get_seq(value))> int(ack_rec)]	
				else:
					#repeat ack
					window.append(p)
				dummy = 0
				#seq, ack_num, syn, ack_bit, fin, data
				p_ack = new_packet(dummy, str(ack_rec),False, True, False,"ack back")
				receiver.sendto(str(p_ack), (sender_host, sender_port))
		else:
			print "other state?"


def write_to_file(filename, buffer):
	global tot_data
	tot_data += len(buffer)
	with open(filename, "a") as myfile:
		myfile.write(buffer)

main()
