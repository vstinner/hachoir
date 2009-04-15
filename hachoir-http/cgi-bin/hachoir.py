#!/usr/bin/python
"""CGI Script performing main functions of hachoir-http.

Author: Robert Xiao
Creation date: June 28 2007

"""

import sys # for stdout, stderr, argv
import os # for environ, listdir, stat, unlink
import time # for time
import hashlib # for md5
import random # for random
import cPickle
from cStringIO import StringIO

from Cookie import SimpleCookie
import cgi
import cgitb; cgitb.enable()

from hachoir_core.tools import alignValue
from hachoir_core.field import Field, SubFile
from hachoir_core.stream import FileInputStream, StringInputStream
from hachoir_core.stream.input import FileFromInputStream, InputSubStream
from hachoir_parser.guess import guessParser

# from http://code.activestate.com/recipes/273844/
try: # Windows needs stdio set for binary mode.
    import msvcrt
    msvcrt.setmode (0, os.O_BINARY) # stdin  = 0
    msvcrt.setmode (1, os.O_BINARY) # stdout = 1
except ImportError:
    pass

# settings
tmp_dir = 'files/'
prune_age = 3600 # seconds
prune_freq = 30 # seconds
# force the use of references for substreams?
# with this on, disk usage will (probably) decrease, but pages (may) take
# longer to load. It's up to you :)
force_substream_ref = True

# global init
script_name = os.environ.get('SCRIPT_NAME', sys.argv[0])

# display utility functions
def bits2hex(n):
    """Transform a measurement in bits to one in bytes, using hexadecimal.

    Example:
    >>> bits2hex(15)
    '00000001.7'

    """
    return '%08X.%s'%divmod(n, 8)

def bits2dec(n):
    """Transform a measurement in bits to one in bytes, using decimal.

    Example:
    >>> bits2dec(15)
    '1.7'

    """
    return '%s.%s'%divmod(n, 8)


# file handling functions
def prune_old():
    """Prune old files to keep things clean

    arguments:
    prune_age is the maximum age of files to keep in seconds
    prune_freq is the minimum time between prunes (as this function is
        executed only when the script is invoked, the actual time between
        prunes may be much greater, but no less, than this value)

    """
    try:
        check = open(tmp_dir+'last_prune')
        last_prune = float(check.read())
        check.close()
    except IOError:
        last_prune = 0.

    if time.time()-last_prune < prune_freq:
        return
    for i in os.listdir(tmp_dir):
        res = os.stat(tmp_dir+i)
        last_time = res.st_atime or res.st_ctime
        if time.time()-last_time>prune_age:
            os.unlink(tmp_dir+i)
    check = open(tmp_dir+'last_prune','w')
    check.write(str(time.time()))

def save_data(data, sessid):
    """Save the persistent storage variable "data" for a given session."""
    f = open(tmp_dir+sessid+'.sess','wb')
    try:
        cPickle.dump(data, f, -1)
    except Exception:
        f.close()
        raise
    f.close()

# form utility functions
def get_sessid():
    """Obtain a session ID from the cookie sent.

    Note that this will fail on non-alphanumeric session IDs
    to prevent possible security problems.

    """
    c = SimpleCookie(os.environ.get('HTTP_COOKIE',''))
    if 'sess' in c and c['sess'].value.isalnum():
        return c['sess'].value
    return ''

def get_parser(data, streamdata, sessid):
    """Guess or retrieve the parser based on the stream.

    Streams are retrieved from the "data" persistant storage variable, from
    the "streams" key.

    The parser for the main stream ((None, None, filename) in data['streams'])
    is cached for efficiency reasons in data['parser_cache'].

    """
    # must remake parser EVERY TIME because parsers can't be pickled
    # (they contain generators which are currently not pickleable)
    # best I can do here is cache the parser, so at least we're not
    # taking time to re-guess the parser...
    if streamdata[0] is None: # original file
        stream = FileInputStream(data['filename'],
                            real_filename = unicode(tmp_dir+sessid+'.file'))
        if 'parser_cache' in data:
            parser = data['parser_cache'](stream)
        else:
            parser = guessParser(stream)
            if not parser:
                print_parse_error()
                return (None, None)
            data['parser_cache'] = parser.__class__
            save_data(data, sessid)
    elif isinstance(streamdata[0], tuple):
        prevstream, prevparser = get_parser(data, streamdata[0], sessid)
        stream = prevparser[streamdata[1]].getSubIStream()
        parser = guessParser(stream)
    else:
        stream = StringInputStream(streamdata[1])
        stream.tags = streamdata[0]
        parser = guessParser(stream)
    return stream, parser


# HTML printing functions
def print_form(msg = ''):
    """Produce file upload form

    msg is an optional message to display
        the message will appear with the CSS class "notice"

    """
    print 'Content-Type: text/html'
    print
    print '''<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
    <title>Hachoir -- Upload a file</title>
    <link rel="stylesheet" type="text/css" href="/hachoir-style.css" />
  </head>
  <body>
    <span id="notice">%s</span><br/>
    <span id="warning">4 MB Limit -- File will be truncated past that!
    </span><br/>
    <form action="%s" method="POST" enctype="multipart/form-data"\
 class="fileform">
      <input type="file" name="file" />
      <input type="submit" value="Upload"/>
    </form>
  </body>
</html>'''%(msg, script_name)

def print_page():
    """Produce and print the main AJAX framing page

    The page produced will handle the AJAX requests and frame them in a div.

    """
    def checkbox(name, desc):
        """A check box which fires an AJAX event when changed."""
        return '''<input type="checkbox" id="check_%s" \
onClick="setOpt('%s')">%s</input>'''%(name, name, desc)
    print 'Content-Type: text/html'
    print
    print '''<html>
<head>
    <title>Hachoir</title>
    <meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
    <script src="/hachoir-client.js" type="text/javascript"></script>
    <link rel="stylesheet" type="text/css" href="/hachoir-style.css" />
</head>
<body onload="doInit();">
    <div id="status" style="display:none">Loading...</div>
    <div id="maincontent"></div>
    <div id="settings">
        <form action="#">
            '''+checkbox('raw','Raw Display')+'''<br/>
            '''+checkbox('hex','Show Hex Addresses/Sizes')+'''<br/>
            '''+checkbox('rel','Show Relative Addresses')+'''
        </form>
        <hr/>
        <span id="warning">4 MB Limit -- File will be truncated past that!
        <br/></span>
        <form action="%s" method="POST" enctype="multipart/form-data" \
class="fileform">
            <input type="file" name="file" />
            <input type="submit" value="Upload new file (overwrite current)"/>
        </form>
    </div>
</body>
</html>'''%script_name

def print_error(msg, eclass='error', print_headers=True):
    """Print an error message.

    msg is the message,
    eclass is the CSS class to use (default 'error'),
    print_headers determines whether HTTP headers are printed (default true)

    """
    if print_headers:
        print 'Content-Type: text/html'
        print
    print '''<h3 class="%s">%s</h3>'''%(eclass, msg)

def print_parse_error():
    """Print a parser error as HTML, using CSS class "parseerror".

    This error could be a failure to parse a file, a potential problem with
    the file, etc.

    """
    print_error('File is not recognized. Error(s) encountered:')
    print '<pre class="parseerror">'+sys.stderr.getvalue()+'</pre>'

def print_path(path, data, stream_id):
    """Print a clickable bar of the current field path.

    filename is the filename to prefix to the path,
    path is a string of the path starting with '/'.

    """
    print '''<span class="path">'''
    if len(data['streams']) > 1:
        print '''<span onClick="delStream('%i')" class="pathlink">'''\
            '''delete current stream</span>'''%stream_id
    print '''<select onChange="opts['stream']=this.value;doPost();">'''
    print '<optgroup label="Select a stream...">'
    for index, stream in enumerate(data['streams']):
        if index == stream_id:
            opt='<option value="%i" selected>%s</option>'
        else:
            opt='<option value="%i">%s</option>'
        print opt%(index, stream[2])
    print '</optgroup></select>'
    print '<span onClick="goPath(\'/\')" class="pathlink">/</span>'
    cur = '/'
    for i in path.strip('/').split('/'):
        if not i:
            continue
        cur += i+'/'
        print '<span onClick="goPath(\'%s\')"\
 class="pathlink">%s/</span>'%(cur, i)
    print '''</span>'''


def handle_form():
    """Process submitted data.

    See comments for details.

    """
    prune_old()
    form = cgi.FieldStorage()
    if 'file' in form and form['file'].file:
        # compute session id
        sessid = get_sessid()
        if not sessid:
            rand = str(time.time())+form['file'].filename+str(random.random())
            sessid = hashlib.md5(rand).hexdigest()
        # write uploaded file
        f = open(tmp_dir+sessid+'.file','wb')
        if form['file'].done==-1:
            raise ValueError("File upload canceled?")
        while f.tell()<2**22: # 4MB limit
            chunk = form['file'].file.read(32768) # 32KB chunks
            if not chunk:
                break
            f.write(chunk)
        if f.tell() == 0:
            f.close()
            print_form('Nothing uploaded.')
            return
        f.close()
        # write session variables
        try:
            fn = unicode(form['file'].filename,'utf-8')
        except UnicodeDecodeError:
            fn = unicode(form['file'].filename,'iso-8859-1')
        # stream "None" represents the original stream
        save_data({'filename':fn,'streams':[(None, None, fn)]}, sessid)
        # send session id and reset variables
        c = SimpleCookie()
        c['sess'] = sessid
        c['hpath'] = '/' # clear path var.
        c['stream'] = '0' # clear stream var
        print c # send cookie to client (headers)
        print_page() # print AJAX frame page
    elif get_sessid(): # or perhaps you already have a file to parse?
        if not 'hpath' in form:
            print_page()
            return
        # redirect stderr, so we can catch parser errors
        sys.stderr = StringIO()
        # load variables
        hpath = cgi.escape(form.getfirst('hpath','/'))
        stream_id = int(form.getfirst('stream','0'))
        path = hpath.split(':')[stream_id]
        sessid = get_sessid()
        try:
            data = cPickle.load(file(tmp_dir+sessid+'.sess','rb'))
        except IOError:
            print_error('Your file was deleted due to inactivity. '
                'Please upload a new one.')
            return
        stream, parser = get_parser(data, data['streams'][stream_id], sessid)
        if parser is None:
            return # sorry, couldn't parse file!
        if 'save' in form:
            # "Download Raw"
            f = FileFromInputStream(stream)
            fld = parser[path]
            f.seek(fld.absolute_address/8)
            size = alignValue(fld.size, 8)/8
            sys.stdout.write('Content-Type: application/octet-stream\r\n')
            sys.stdout.write('Content-Length: %i\r\n'%size)
            sys.stdout.write('Content-Disposition: attachment; '
                'filename=%s\r\n\r\n'%path.strip('/').split('/')[-1])
            sys.stdout.write(f.read(size))
            return
        elif 'savesub' in form:
            # "Download Substream"
            stream = parser[path.rstrip('/')].getSubIStream()
            filename = path.strip('/').split('/')[-1]
            tags = getattr(stream,'tags',[])
            for tag in tags:
                if tag[0] == 'filename':
                    filename = tag[1]
            sys.stdout.write('Content-Type: application/octet-stream\r\n')
            sys.stdout.write('Content-Disposition: attachment; '
                'filename=%s\r\n\r\n'%filename)
            sys.stdout.write(FileFromInputStream(stream).read())
            return
        elif 'addStream' in form:
            # "Parse Substream"
            spath = cgi.escape(form['addStream'].value)
            new_stream = parser[spath.rstrip('/')].getSubIStream()
            streamdata = FileFromInputStream(new_stream).read()
            new_parser = guessParser(new_stream)
            if new_parser:
                stream = new_stream
                parser = new_parser
                tags = getattr(stream,'tags',[])
                streamname = data['streams'][stream_id][2]+':'
                data['streams'].append((tags, streamdata, streamname+spath))
                try:
                    if force_substream_ref:
                        raise Exception("Use references for all substreams")
                    save_data(data, sessid)
                except Exception:
                    # many things could go wrong with pickling
                    data['streams'][-1] = (data['streams'][stream_id],
                        spath, streamname+spath)
                    save_data(data, sessid)
                path = '/'
                hpath += ':/'
                stream_id = len(data['streams'])-1
            else:
                sys.stderr.write("Cannot parse substream %s: "
                    "No suitable parser\n"%spath)
        elif 'delStream' in form:
            # "Delete Stream"
            n = int(form['delStream'].value)
            paths = hpath.split(':')
            del paths[n]
            del data['streams'][n]
            if n >= len(data['streams']):
                stream_id = 0
            else:
                stream_id = n
            path = paths[stream_id]
            hpath = ':'.join(paths)
            save_data(data, sessid)
            stream, parser = get_parser(data, data['streams'][stream_id],
                sessid)
        # update client's variables
        c = SimpleCookie()
        c['hpath'] = hpath
        c['stream'] = str(stream_id)
        print c # send cookie to client
        # send headers
        print 'Content-Type: text/html'
        print
        # breadcrumb trail path up top
        print_path(path, data, stream_id)
        # fields
        print '''<table id="maintable" border="1">
<tr class="header">
    <th class="headertext">Offset</th>
    <th class="headertext">Name</th>
    <th class="headertext">Type</th>
    <th class="headertext">Size</th>
    <th class="headertext">Description</th>
    <th class="headertext">Data</th>
    <th class="headertext">Download Field</th>
</tr>'''
        for i in parser[path]:
            # determine options
            display = i.raw_display if form.getfirst('raw','0') == '1'\
                else i.display
            disp_off = bits2hex if form.getfirst('hex','0') == '1'\
                else bits2dec
            addr = i.address if form.getfirst('rel','0') == '1'\
                else i.absolute_address
            if display == 'None':
                display = ''
            # clickable name for field sets
            if i.is_field_set:
                name = '''<span href="#" onClick="goPath('%s%s/')"\
 class="fieldlink">%s/</span>'''%(path, i.name, i.name)
            else:
                name = i.name
            print '<tr class="data">'
            print '<td class="fldaddress">%s</td>'%disp_off(addr)
            print '<td class="fldname">%s</td>'%name
            print '<td class="fldtype">%s</td>'%i.__class__.__name__
            print '<td class="fldsize">%s</td>'%disp_off(i.size)
            print '<td class="flddesc">%s</td>'%i.description
            print '<td class="flddisplay">%s</td>'%display
            print '<td class="flddownload">'
            paths = hpath.split(':')
            paths[stream_id] += i.name
            url = "%s?hpath=%s&stream=%s"%\
                (script_name,':'.join(paths), stream_id)
            # hack to determine if a substream is present
            # the default getSubIStream() returns InputFieldStream()
            # InputFieldStream() then returns an InputSubStream.
            # in all the overrides, the return is a different stream type,
            # but this is certainly not the safest way to check for
            # an overridden method...
            # finally, if the field is a SubFile, then it has a custom
            # substream, and thus gets the substream features.
            if not isinstance(i.getSubIStream(), InputSubStream)\
                or isinstance(i, SubFile):
                print '<a href="javascript:addStream(\'%s\')"\
 class="dllink">Parse Substream</a><br/>'%(path+i.name)
                print '<a href="%s&savesub=1"\
 class="dllink">Download Substream</a><br/>'%url
                print '<a href="%s&save=1"\
 class="dllink">Download Raw</a>'%url
            else:
                print '<a href="%s&save=1"\
 class="dllink">Download</a>'%url
            print '</td>'
            print '</tr>'
        print '</table>'
        print_path(path, data, stream_id)
        if sys.stderr.getvalue():
            print_error('Error(s) encountered:', print_headers=False)
            print '<pre class="parseerror">%s</pre>'%sys.stderr.getvalue()
    else:
        print_form('Note: Cookies MUST be enabled!')

handle_form()
