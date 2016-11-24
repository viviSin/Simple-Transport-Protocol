#Sender.py
#2.7.3

import socket, sys, time,random
from packet import *
from random import randint

STATE_IDLE = 0
STATE_ESTAB = 1
STATE_TERMINATE = 2
STATE_WAIT = 3 
STATE_END = 4 
state = STATE_IDLE

tot_segment = 0
tot_data = 0
tot_drop = 0
tot_retransmit = 0
tot_dup_ack = 0

def main():
	global state
		
	# receiver_host = str(sys.argv[1])
	# receiver_port = int(sys.argv[2])
	# filename = str(sys.argv[3])
	# mws = int(sys.argv[4])  #max window size
	# mss = int(sys.argv[5])  #max segmanet size
	# timeout_in = float(sys.argv[6])
	# pdrop = float(sys.argv[7]) #packetdrop probability
	# seed = int(sys.argv[8])

	receiver_host      = "localhost"
	receiver_port    = 7239
	filename   = "test2.txt"
	mws          = 500
	mss          = 50
	timeout_in       = 3
	pdrop     = 0.3
	seed         = 300
	
	global tot_data
	global tot_segment  
	global tot_drop  
	global tot_retransmit  
	global tot_dup_ack  

	timeout = timeout_in
	start = time.time()*1000
	sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sender.settimeout(1)
	log = open('Sender_log.txt','w')
	log.close()
	log = open('Sender_log.txt','a')
	
	handshake(log,start,sender, receiver_host, receiver_port)
	
	#read txt file in 
	try:
		descriptor = open(filename, "r")
		buffer = descriptor.read()
		descriptor.close()
	except:
		sys.exit("fail to read file")

	data_send(log,start,sender, receiver_host, receiver_port,buffer,mws,mss,pdrop,seed,timeout)
	termination(log,start,sender, receiver_host, receiver_port)


def termination(log,start,sender, receiver_host, receiver_port):
	global state
	global tot_data  
	global tot_segment  
	global tot_drop  
	global tot_retransmit  
	global tot_dup_ack  
	xseq = randint(1,9)
	#seq, ack_num, syn, ack_bit, fin, data
	p1 = new_packet( str(xseq), 0, False, False, True, "")
	addr = (receiver_host, receiver_port)
	sender.sendto(str(p1), addr)
	curr_time = time.time()*1000-start
	msg = 'snd\t'+str(curr_time)+'\tF\t'+str(xseq)+'\t'+str(len(get_data(p1)))+'\t'+str(get_ack(p1))+'\n'
	log.write(msg)
	
	while True:
		try:
			response, addr = sender.recvfrom(1024)
			p2 = eval(response)

			if (is_fin(p2) and not is_ack(p2)):
				#seq, ack_num, syn, ack_bit, fin, data
				p4 = new_packet( 0, str(int(get_seq(p2))+1), False, True, True, "")
				state = STATE_END
				sender.sendto(str(p4), addr)
				curr_time = time.time()*1000-start
				msg = 'snd\t'+str(curr_time)+'\tA\t'+str(get_seq(p4))+'\t'+str(len(get_data(p4)))+'\t'+str(get_ack(p4))+'\n'
				log.write(msg)
	
				t1 = 'Amount of data transferred: '+str(tot_data)+' bytes\n'
				t2 = 'Number of data segments sent: '+str(tot_segment)+'\n'
				t3 = 'Number of packets dropped: '+str(tot_drop)+'\n'
				t4 = 'Number of retransmitted segments: '+str(tot_retransmit)+'\n'
				t5 = 'Number of duplicate acknowledgements: '+str(tot_dup_ack)+'\n'
				
				log.write(t1)
				log.write(t2)
				log.write(t3)
				log.write(t4)
				log.write(t5)
				log.close()
				sys.exit()
			else :
				curr_time = time.time()*1000-start
				msg = 'rcv\t'+str(curr_time)+'\tFA\t'+str(get_seq(p2))+'\t'+str(len(get_data(p2)))+'\t'+str(get_ack(p2))+'\n'
				log.write(msg)
		except socket.timeout:
			print ("timed out in terminate")
			sys.exit()


def data_send(log,start,sender, receiver_host, receiver_port,buffer,mws,mss,pdrop,seed,timeout):
	global tot_segment  
	global tot_drop  
	global tot_retransmit  
	global tot_dup_ack

	base_time = time.time()*1000
	window_base = -1 #compare to seq in window[0] 
	seq = 0; #seq start from 0, easier to debug
	window = []
	dummy = 0
	random.seed(seed)
	count = 0
	pre_ack = -1
	addr = (receiver_host, receiver_port)
	while (True):
		window_size = mws/mss

		while (not window or len(window) < window_size and seq <= len(buffer)):
			if((time.time()*1000-base_time >=  timeout) and len(window)>0 and int(window_base) == int(get_seq(window[0]))):
				#timeout event
				base_time = time.time()*1000
				tot_retransmit+=1
				if ((int(get_seq(window[0])) + mss) < len(buffer)):
					data_segment = buffer[int(get_seq(window[0])):int(get_seq(window[0]))+mss]
				else:
					data_segment = buffer[int(get_seq(window[0])):]
				p = new_packet(int(get_seq(window[0])), 0, False, False, False, data_segment)
				PLD(log,start,sender, p, addr,pdrop)

			if ((seq + mss) < len(buffer)):
				data_segment = buffer[seq:seq+mss]
			else:
				data_segment = buffer[seq:]
			p = new_packet(seq, dummy, False, False, False, data_segment)
			window.append(p)
			window_base = int(get_seq(window[0]))

			seq = seq + mss
			PLD(log,start,sender, p, addr,pdrop)

		try:
			response, addr = sender.recvfrom(1024)
			p_rec = eval(response)
			curr_time = time.time()*1000-start
			msg = 'rcv\t'+str(curr_time)+'\tA\t'+str(get_seq(p_rec))+'\t'+str(len(get_data(p_rec)))+'\t'+str(get_ack(p_rec))+'\n'
			log.write(msg)
			#del the success ack
			if is_ack(p_rec):
				max_ack = get_seq(window[len(window)-1]) 
				if(int(get_ack(p_rec)) >= len(buffer)):
					state = STATE_TERMINATE
					break
				if(pre_ack==int(get_ack(p_rec))):
					count += 1
					tot_dup_ack += 1
				if (count >= 2):
					re_transmit(log,start,sender, addr,pdrop,get_ack(p_rec),window,mss,buffer)
					count = 0

				pre_ack = int(get_ack(p_rec))
				for value in window:
					if int(int(get_seq(value))+int(len(get_data(value))))> int(get_ack(p_rec)):
						base_time = time.time()*1000
				window[:] = [value for value in window if int(int(get_seq(value))+int(len(get_data(value))))> int(get_ack(p_rec))]

			 
		except socket.timeout:
			if ((int(get_seq(window[0])) + mss) < len(buffer)):
				data_segment = buffer[int(get_seq(window[0])):int(get_seq(window[0]))+mss]
			else:
				data_segment = buffer[int(get_seq(window[0])):]
			p = new_packet(int(get_seq(window[0])), 0, False, False, False, data_segment)
			PLD(log,start,sender, p, addr,pdrop)

def re_transmit(log,start,sender, addr,pdrop,seq,window,mss,buffer):
	global tot_segment  
	global tot_drop  
	global tot_retransmit  
	global tot_dup_ack
	if ((int(seq) + mss) < len(buffer)):
		data_segment = buffer[int(seq):int(seq)+mss]
	else:
		data_segment = buffer[int(seq):]
	p = new_packet(int(seq), 0, False, False, False, data_segment)
	tot_retransmit+=1
	PLD(log,start,sender, p, addr,pdrop)
	


def PLD(log,start,sender, p, addr,pdrop):
	global tot_segment  
	global tot_data  
	global tot_drop  
	global tot_retransmit  
	global tot_dup_ack
	rand = random.random()
	tot_segment +=1
	if (rand > pdrop):
		sender.sendto(str(p), addr)
		tot_data += len(get_data(p))
		curr_time = time.time()*1000-start
		msg = 'snd\t'+str(curr_time)+'\tD\t'+str(get_seq(p))+'\t'+str(len(get_data(p)))+'\t'+str(get_ack(p))+'\n'
		log.write(msg)
	else:
		tot_drop += 1
		curr_time = time.time()*1000-start
		msg = 'drop\t'+str(curr_time)+'\tD\t'+str(get_seq(p))+'\t'+str(len(get_data(p)))+'\t'+str(get_ack(p))+'\n'
		log.write(msg)


def handshake(log,start,sender, receiver_host, receiver_port):
	global state
	if (state != STATE_IDLE):
		print "not ready for handShake in sender"
		sys.exit()
	
	xseq = randint(1,9)
	#seq, ack_num, syn, ack_bit, fin, data
	p1 = new_packet( str(xseq), 0, True, False, False, "")
	addr = (receiver_host, receiver_port)
	sender.sendto(str(p1), addr)
	
	curr_time = time.time()*1000-start
	msg = 'snd\t'+str(curr_time)+'\tS\t'+str(xseq)+'\t'+str(len(get_data(p1)))+'\t'+str(get_ack(p1))+'\n'
	log.write(msg)
	
	try:
		response, addr = sender.recvfrom(1024)
		p2 = eval(response)

		if(state == STATE_IDLE):

			if (is_syn(p2) and is_ack(p2) and (int(get_ack(p2)) == (xseq+1))):
				
				curr_time = time.time()*1000-start
				msg = 'rcv\t'+str(curr_time)+'\tSA\t'+str(get_seq(p2))+'\t'+str(len(get_data(p2)))+'\t'+str(get_ack(p2))+'\n'
				log.write(msg)
	
				p3 = new_packet(0, str(int(get_seq(p2))+1), False, True, False, "")
				state = STATE_ESTAB
				addr = (receiver_host, receiver_port)
				sender.sendto(str(p3), addr)

				curr_time = time.time()*1000-start
				msg = 'snd\t'+str(curr_time)+'\tA\t'+str(get_seq(p3))+'\t'+str(len(get_data(p3)))+'\t'+str(get_ack(p3))+'\n'
				log.write(msg)
				return
			else :
				print "receiver have problem in handshake"
		


	except socket.timeout:
		print ("timed out in handShake")
		sys.exit()


main()
