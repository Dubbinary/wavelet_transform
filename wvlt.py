import time
import sys
import cli_dispatcher

print("[==== Wavelet transformation program ====]")
time_begin = time.time()
cli_dispatcher.cdisp(sys.argv[1:])
time_end = time.time()
print("Time of processing: "+str(time_end-time_begin)+' seconds')
print("[==== Exit fom program ====]")