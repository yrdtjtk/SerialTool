#-*- coding:utf-8 -*-

from PyCRC.CRCCCITT import CRCCCITT

def hexstr2buf(s):
	b = bytearray(len(s)//2)
	for i in range(len(b)):
		s1 = s[i*2:i*2+2]
		i1 = int(s1, 16)
		b[i] = i1
	return bytes(b)

# def hex2asc(h):
# 	if 0<=h and h<=9:
# 		return chr(h+ord('0'))
# 	elif 0x0A<=h and h<=0x0F:
# 		return chr(h+ord('A')-0x0A)
# 	else:
# 		raise Exception('Invalid Argument,must be 0x00~0x0F!')

# def buf2hexstr(b):
# 	sa = []
# 	for b1 in b:
# 		sa.append(hex2asc(b1//16))
# 		sa.append(hex2asc(b1%16))
# 	return ''.join(sa)

def buf2hexstr(b):
	sa = []
	for b1 in b:
		sa.append('%02X' % b1)
	return ''.join(sa)

def crc(data):
	return CRCCCITT().calculate(data)