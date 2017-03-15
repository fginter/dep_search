import glob
import sys
import time
import os
def main():

    limit = 3600
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            limit = 3600

    while(True):
        files = []
        files.extend(glob.glob('./qry*.pyx'))
        files.extend(glob.glob('./qry*.so'))
        files.extend(glob.glob('./qry*.cpp'))

        for f in files:
            file_age = time.time() - os.path.getctime(f)
            if file_age > limit:
                os.remove(f)

main()
