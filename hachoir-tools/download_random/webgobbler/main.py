#!/usr/bin/env python

total = 100
directory = "imagepool"

from webgobbler import imagePool, applicationConfig
from time import sleep

config = applicationConfig()
config["pool.keepimages"] = True
config["pool.imagepooldirectory"] = directory
config["pool.nbimages"] = total
pool = imagePool(config=config)
try:
    try:
        pool.start()
        count = 0
        while True:
            image = pool.getImage()
            if image:
                count += 1
                print "Downloaded: %s/%s" % (count, total)
                if total <= count:
                    break
            else:
                sleep(1.0)
    except KeyboardInterrupt:
        print "Interrupt."
finally:
    print "Stopping image pool (please wait)."
    pool.shutdown()
    pool.join()


