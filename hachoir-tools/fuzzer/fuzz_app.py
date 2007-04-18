from os import nice, mkdir, path, unlink, listdir
from application import Application
from array import array
from mangle import mangle
from time import sleep
from md5 import md5
from random import randint
from hachoir_core.timeout import limitedTime, Timeout

APP = "identify"
APP_ARGS = ["-v"]
TIMEOUT = 30.0

def cleanupDir(dirname):
    try:
        files=listdir(dirname)
    except OSError:
        return
    for file in files:
        filename = path.join(dirname, file)
        unlink(filename)

class Fuzzer:
    def __init__(self, original):
        self.original = original
        self.data = open(self.original, 'rb').read()
        assert 1 <= len(self.data)

    def fuzzFile(self, filename):
        if True:
            app = Application("clamscan", filename)
        else:
            app = Application("/opt/magick/bin/identify", ["-verbose", filename])
        app.start()
        try:
            limitedTime(TIMEOUT, app.wait)
        except Timeout:
            print "Timeout error!"
            app.stop()
            return True
        except KeyboardInterrupt:
            print "Interrupt!"
            app.stop()
            return True
        return app.exit_failure

    def info(self, message):
        if False:
            print message

    def warning(self, message):
        print "WARN: %s" % message

    def mangle(self, filename):
        self.info("Mangle")
        data = array('B', self.data)

        if randint(0, 4) == 0:
            size = randint(1, len(self.data)-1)
            print "@@ Truncate to %s bytes" % size
            data = data[:size]

        percent = randint(1, 10) / 100.0
        count = mangle(data, percent)
        self.warning("Mangle: %s" % count)
        self.info("Output MD5: %s" % md5(data).hexdigest())

        self.info("Write to %s" % filename)
        output = open(filename, 'wb')
        data = data.tofile(output)
        output.close()


    def run(self):
        ext = self.original[-3:]
        tmp_name = '/tmp/image.%s' % ext
        dir = "/tmp/fuzz.clamav"
        try:
            cleanupDir(dir)
            try:
                mkdir(dir)
            except OSError:
                pass
            while True:
                if True:
                    files = []
                    for index in xrange(50):
                        tmp_name = path.join(dir, 'image.%u.%s' % (index, ext))
                        self.mangle(tmp_name)
                        files.append(tmp_name)
                else:
                    self.mangle(tmp_name)
                    files = [tmp_name]

                print "============= Run Test ==============="
                if self.fuzzFile(files):
                    print "Fuzzing error: stop!"
                    break
                print "Test: ok"
#                sleep(0.250)
        except KeyboardInterrupt:
            print "Interrupt."

def main():
    nice(19)
    #image = "/home/haypo/testcase/logo-kubuntu.png"
    #image = "/home/haypo/testcase/jpeg.exif.photoshop.jpg"
    #image = "/home/haypo/testcase/usa_railroad.jpg"
    #image = "/home/haypo/testcase/article01.bmp"
#    image = "/home/haypo/testcase/hero.tga"
#    image = "/home/haypo/testcase/cross.xcf"
    #image = "/home/haypo/testcase/wormux_32x32_16c.ico"
    #image = "/home/haypo/testcase/deja_vu_serif-2.7.ttf"
    #document = "/home/haypo/testcase/eula.exe"
    #document = "/home/haypo/mytestcase/msoffice/002.PPS"
    document = "/home/haypo/fuzzing/clamav/002.pps"
#    document = "/home/haypo/mytestcase/exe/chiencontrechat.exe"
    fuzzer = Fuzzer(document)
    fuzzer.run()

if __name__ == "__main__":
    main()

