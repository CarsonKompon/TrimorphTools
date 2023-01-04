import struct

def read_string(stream):
    length = stream.read(2)
    length = int.from_bytes(length, byteorder='big')
    string = stream.read(length)
    return string.decode("utf-8")

def read_char(stream):
    return int.from_bytes(stream.read(2), byteorder='big')

def read_int(stream):
    return int.from_bytes(stream.read(4), byteorder='big')

def read_short(stream):
    return int.from_bytes(stream.read(2), byteorder='big')

def read_long(stream):
    return int.from_bytes(stream.read(8), byteorder='big')

def read_bool(stream):
    return stream.read(1) == b'\x01'

def read_float(stream):
    return struct.unpack('>f', stream.read(4))[0]

def read_byte(stream):
    return int.from_bytes(stream.read(1), byteorder='big')
