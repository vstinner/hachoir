#!/usr/bin/python
''' server module for hachoir '''

import sys,os,time
import hashlib,random
import cPickle
from cStringIO import StringIO

from Cookie import SimpleCookie
import cgi
import cgitb; cgitb.enable()

from hachoir_core.tools import alignValue
from hachoir_core.field import Field
from hachoir_core.stream.input import FileFromInputStream,InputSubStream
from hachoir_parser.guess import createParser

# settings
tmp_dir='files/'
prune_age=3600 # seconds
prune_freq=30 # seconds

# global init
script_name=os.environ.get('SCRIPT_NAME', sys.argv[0])

def prune_old():
    ''' Prune old files to keep things clean

    arguments:
    prune_age is the maximum age of files to keep in seconds
    prune_freq is the minimum time between prunes (as the script does not
        run all the time, it cannot define a maximum time)

    '''
    try:
        check=open(tmp_dir+'last_prune')
        last_prune=float(check.read())
        check.close()
    except IOError:
        last_prune=0.

    if time.time()-last_prune < prune_freq:
        return
    for i in os.listdir(tmp_dir):
        res=os.stat(tmp_dir+i)
        last_time=res.st_atime or res.st_ctime
        if time.time()-last_time>prune_age:
            os.unlink(tmp_dir+i)
    check=open(tmp_dir+'last_prune','w')
    check.write(str(time.time()))

def print_form(msg=''):
    ''' Produce file upload form

    msg is an optional message to display
        the message will appear as the CSS class "notice"

    '''
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
</html>'''%(msg,script_name)

def print_page():
    ''' Produce and print the main AJAX framing page

    The page produced will handle the AJAX requests and frame them in a div.

    '''
    def checkbox(name,desc):
        return '''<input type="checkbox" id="check_%s" \
onClick="setOpt('%s')">%s</input>'''%(name,name,desc)
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
        <span id="warning">4 MB Limit -- File will be truncated past that!<br/>
        </span>
        <form action="%s" method="POST" enctype="multipart/form-data" \
class="fileform">
            <input type="file" name="file" />
            <input type="submit" value="Upload new file (overwrite current)"/>
        </form>
    </div>
</body>
</html>'''%script_name

def print_error(msg,eclass='error',print_headers=True):
    ''' Print an error message.

    msg is the message,
    eclass is the CSS class to use (default 'error'),
    print_headers determines whether HTTP headers are printed (default true)

    '''
    if print_headers:
        print 'Content-Type: text/html'
        print
    print '''<h3 class="%s">%s</h3>'''%(eclass,msg)

def get_sessid():
    ''' Obtain a session ID from the cookie sent.

    Note that this will fail on non-alphanumeric session IDs
    to prevent possible security problems.

    '''
    c=SimpleCookie(os.environ.get('HTTP_COOKIE',''))
    if 'sess' in c and c['sess'].value.isalnum():
        return c['sess'].value
    return ''

def print_path(filename,path):
    ''' Print a clickable bar of the current field path.

    filename is the filename to prefix to the path,
    path is a string of the path starting with '/'.

    '''
    print '''<span class="path">'''
    print '<span onClick="goPath(\'/\')" class="pathlink">%s</span>/'%filename.encode('utf-8')
    cur='/'
    for i in path.strip('/').split('/'):
        if not i: continue
        cur+=i+'/'
        print '<span onClick="goPath(\'%s\')"\
 class="pathlink">%s</span>/'%(cur,i)
    print '''</span>'''

def bits2hex(n):
    ''' Transform a measurement in bits to one in bytes, using hexadecimal.

    Example:
    >>> bits2hex(15)
    '00000001.7'

    '''
    return '%08X.%s'%divmod(n,8)

def bits2dec(n):
    ''' Transform a measurement in bits to one in bytes, using decimal.

    Example:
    >>> bits2dec(15)
    '1.7'

    '''
    return '%s.%s'%divmod(n,8)

def handle_form():
    ''' Process submitted data.

    See comments for details.

    '''
    prune_old()
    form=cgi.FieldStorage()
    if 'file' in form and form['file'].file:
        # compute session id
        sessid=get_sessid()
        if not sessid:
            rand=str(time.time())+form['file'].filename+str(random.random())
            sessid=hashlib.md5(rand).hexdigest()
        # write uploaded file
        f=open(tmp_dir+sessid+'.file','wb')
        while f.tell()<2**22: # 4MB limit
            chunk = form['file'].file.read(2**15) # 32KB chunks
            if not chunk: break
            f.write (chunk)
        if f.tell()==0:
            f.close()
            print_form('Nothing uploaded.')
            return
        f.close()
        # write session variables
        f=open(tmp_dir+sessid+'.sess','wb')
        try: fn=unicode(form['file'].filename,'utf-8')
        except UnicodeDecodeError: fn=unicode(form['file'].filename,'iso-8859-1')
        cPickle.dump({'filename':fn},f,-1)
        f.close()
        # send session id cookie to client
        c=SimpleCookie()
        c['sess']=sessid
        c['hpath']='/' # clear path var.
        print c # send cookie to client
        # print AJAX frame page
        print_page()
    elif get_sessid():
        # got a sessid, now check for path var
        if 'hpath' not in form:
            print_page()
            return
        sys.stderr=StringIO()
        # load variables
        path=cgi.escape(form.getfirst('hpath','/'))
        sessid=get_sessid()
        try: data=cPickle.load(file(tmp_dir+sessid+'.sess','rb'))
        except:
            print_error('Your file was deleted due to inactivity. '
                'Please upload a new one.')
            return
        # must remake parser EVERY TIME because parsers can't be pickled
        # (they contain generators which are currently not pickleable)
        parser=createParser(data['filename'],
                            real_filename=unicode(tmp_dir+sessid+'.file'))
        if not parser:
            print_error('File is not recognized. Error(s) encountered:')
            print '<pre class="parseerror">'+sys.stderr.getvalue()+'</pre>'
            return
        if 'save' in form:
            f=open(tmp_dir+sessid+'.file','rb')
            fld=parser[path]
            f.seek(fld.absolute_address/8)
            size=alignValue(fld.size,8)/8
            sys.stdout.write('Content-Type: application/octet-stream\r\n')
            sys.stdout.write('Content-Length: %i\r\n'%size)
            sys.stdout.write('Content-Disposition: attachment; '
                'filename=%s\r\n\r\n'%path.strip('/').split('/')[-1])
            sys.stdout.write(f.read(size))
            f.close()
            return
        elif 'savesub' in form:
            sys.stdout.write('Content-Type: application/octet-stream\r\n')
            sys.stdout.write('Content-Disposition: attachment; '
                'filename=%s\r\n\r\n'%path.strip('/').split('/')[-1])
            stream=parser[path.rstrip('/')].getSubIStream()
            sys.stdout.write(FileFromInputStream(stream).read())
            return
        # send headers
        print 'Content-Type: text/html'
        print
        # breadcrumb trail path up top
        print_path(data['filename'],path)
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
            display=i.raw_display if form.getfirst('raw','0')=='1'\
                else i.display
            disp_off=bits2hex if form.getfirst('hex','0')=='1'\
                else bits2dec
            addr=i.address if form.getfirst('rel','0')=='1'\
                else i.absolute_address
            if display=='None': display=''
            # clickable name for field sets
            if i.is_field_set:
                name='''<span href="#" onClick="goPath('%s%s/')"\
 class="fieldlink">%s/</span>'''%(path,i.name,i.name)
            else: name=i.name
            print '<tr class="data">'
            print '<td class="fldaddress">%s</td>'%disp_off(addr)
            print '<td class="fldname">%s</td>'%name
            print '<td class="fldtype">%s</td>'%i.__class__.__name__
            print '<td class="fldsize">%s</td>'%disp_off(i.size)
            print '<td class="flddesc">%s</td>'%i.description
            print '<td class="flddisplay">%s</td>'%display
            print '<td class="flddownload">'
            # hack to determine if a substream is present
            # the default getSubIStream() returns InputFieldStream()
            # InputFieldStream() then returns an InputSubStream.
            # in all the overrides, the return is a different stream type,
            # but this is certainly not the safest way to check for
            # an overridden method...
            if not isinstance(i.getSubIStream(),InputSubStream):
                print '<a href="%s?hpath=%s%s&savesub=1"\
 class="dllink">Download as Substream</a><br/>'%(script_name,path,i.name)
                print '<a href="%s?hpath=%s%s&save=1"\
 class="dllink">Download Raw</a>'%(script_name,path,i.name)
            else:
                print '<a href="%s?hpath=%s%s&save=1"\
 class="dllink">Download</a>'%(script_name,path,i.name)
            print '</td>'
            print '</tr>'
        print '</table>'
        print_path(data['filename'],path)
        if sys.stderr.getvalue():
            print_error('Error(s) encountered:',print_headers=False)
            print '<pre class="parseerror">'+sys.stderr.getvalue()+'</pre>'
    else:
        print_form('Note: Cookies MUST be enabled!')
handle_form()
