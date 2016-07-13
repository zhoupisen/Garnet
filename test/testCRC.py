__author__ = 'Administrator'
import numpy as np
crc_list1=[0x01,0x09,0x60,0x22,0xb8,0x24,0x01,
           0x00,0x00,0x30,0x34,0x35,0x31,0x30,0x2d,
           0x34,0x30,0x30,0x37,0x35,0x2d,0x30,0x31,
           0x52,0x45,0x56,0x31,
           0x30,0x31,
           0x84,0x03,0x00,0x42]
crc=np.int16(0)
temp1=np.int16(0)
temp2=np.int16(0)
temp3=np.int16(0)

for temp in crc_list1:
    temp1=np.int16(temp)
    temp2=np.left_shift(temp1,8)
    crc=np.int16(np.bitwise_xor(crc,temp2))
    for i in range(8):
        if(np.bitwise_and(crc,0x8000)):
            temp3=np.int16(np.left_shift(crc,1))
            crc=np.int16(np.bitwise_xor(temp3,0x1021))
        else:
            crc=np.int16(np.left_shift(crc,1))


print hex(crc)
