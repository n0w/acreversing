#!/usr/bin/python3

import csv
import argparse
import sys
import struct

THRESHOLD_VOLTAGE = 1.5
THRESHOLD_SAMPLES = 10
vHIGH = 2
vLOW = 1

TOTAL = 0


def outputToFile(fname, packet):
    with open(fname, 'wb') as outFile:
        for byte in packet:
            outFile.write(bytes(byte))


def read_rigol_csv(fname, channel=1):
    # ToDo: Detect if csv file has a header.
    raw_samples = []

    with open(fname, 'rt') as csvfile:
        c = csv.reader(csvfile)

        for row_num, row in enumerate(c):
            if row_num > 2:
                raw_samples.append(float(row[1]))

    return raw_samples


def printBanner():
    print("Olimpia Splendid IR Decoder")
    print("Angel Suarez-B. (n0w) 2016")
    print("===========================")
    print("")

# Assigns a '1' or a '0' by comparing the number of read samples and the promediated long pulse duration
def decode(num_samples, longPulseDuration, reverse):
    if num_samples == 0:
        return

    # Using XOR to reverse symbol assignation
    if (num_samples < (longPulseDuration - longPulseDuration / 2.5)) ^ reverse:
        return '0'
    else:
        return '1'

def printToStdout(packet):
    # Print human friendly binary string
    for byte in packet:

        # Unpacked byte
        unpacked = struct.unpack("B", byte)[0]

        # ASCII bin representation
        binascii = (bin(int(unpacked)))[2:].zfill(8)

        # ASCII hex representation
        hexascii = "0x" + hex(unpacked)[2:].zfill(2)

        print(" |-----[%s]  |  %s" % (binascii, hexascii))

def parseWave(samples, verbosity, reverse, endian):
    decodedBinaryString = ""
    preambleStart = 0
    preambleEnd = 0
    preambleSize = 0
    longPulseDuration = 0
    shortPulseDuration = 0
    packet = []

    # Detect preamble start
    # (!) vHIGH may need to be tuned to achieve proper decoding
    for sample in samples:
        if sample < vHIGH:
            if verbosity:
                print("[+] Preamble start detected! Sample: %d" % preambleStart)
            break
        else:
            preambleStart += 1

    # Detect preamble end
    for sample in samples[preambleStart:]:
        if sample > vLOW:
            preambleEnd = preambleStart + preambleSize
            shortPulseDuration = preambleSize / 11
            longPulseDuration = preambleSize / 3

            if verbosity:
                print("[+] Preamble end detected! Sample: %d" % preambleEnd)
                print(" |------- Preamble duration: %d samples" % preambleSize)
                print(" |---- Short pulse duration: %d samples" % (shortPulseDuration))
                print(" |----  Long pulse duration: %d samples" % (longPulseDuration))

            # Sanity check
            if (shortPulseDuration == 0) or (longPulseDuration == 0) or (preambleSize == 0):
                print("[e] Zero value detected, bad threshold values? Quitting...")
                exit(-1)
            else:
                print("[+] Decoding...")
                break
        else:
            preambleSize += 1

    # Start parsing
    # numSamplesAct will hold the number or read samples prior to a high-to-low transition
    numSamplesAct = 0

    for sample in samples[preambleEnd:]:
        if sample > vHIGH:
            numSamplesAct += 1
        else:
            decoded = decode(numSamplesAct, longPulseDuration, reverse)

            if decoded is not None:
                decodedBinaryString += decoded

            numSamplesAct = 0

    # Rip off START bit
    decodedBinaryString = decodedBinaryString[1:]

    # Print human friendly binary string
    i = 0
    currentByte = ""

    print("[+] Decoded %s bytes" % (len(decodedBinaryString) / 8.0))

    for bit in decodedBinaryString:
        if i < 7:
            currentByte += bit
            i += 1
        else:
            currentByte += bit
            if endian:
                currentByte = currentByte[::-1]
            packet.append(struct.pack("B", int(currentByte, 2)))

            currentByte = ""
            i = 0
    return packet


if __name__ == "__main__":
    printBanner()
    p = argparse.ArgumentParser(description='Extracts values from Rigol CSV.')

    p.add_argument('file', metavar='file', type=str, help='File to process.')
    p.add_argument('-o', '--outfile', nargs='?', type=str, help='Binary output to file.')
    p.add_argument('-v', '--verbosity', action='store_true', help="Print extra information to stdout.")
    p.add_argument('-b', '--batch', type=str, help="Process all csv files in target dir.")
    p.add_argument('-r', '--reverse', action='store_true',
                   help="Assign '1' symbol to short pulses (Defaults to short == '0').")
    p.add_argument('-e', '--endian', action='store_true',
                   help="Toggle endianness.")
    # ToDo: Recursive mode.
    args = p.parse_args()

    print("[+] Opening wave file %s" % args.file)
    samples = read_rigol_csv(args.file)
    packet = parseWave(samples, args.verbosity, args.reverse, args.endian)

    if args.outfile:
        outputToFile(args.outfile, packet)

    if args.verbosity:
        printToStdout(packet)

    print("[+] Done.\n")
