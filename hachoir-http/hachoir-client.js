/* Client-side Javascript for hachoir-http.

Author: Robert Xiao
Creation date: June 28 2007

*/
// ajax from http://en.wikipedia.org/wiki/XMLHttpRequest
function ajax($url, $vars, $object){

    if (XMLHttpRequest){
        var $class = new XMLHttpRequest();
    } else {
        var $class = new ActiveXObject("MSXML2.XMLHTTP.3.0");
    }

    $class.open("POST", $url, true);
    $class.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

    $class.onreadystatechange = function(){
        // purposefully ignore readyState -- partial updates are welcome,
        // as a lot of data may be transferred, so a partial update provides
        // indication of progress.
        if ($class.responseText){
            $obj = $class.responseText;
            $object($obj,$class);
        }
    }
    $class.send($vars);
}

function updateHTML(dat,$class) {
    document.getElementById("maincontent").innerHTML=dat;
    if ($class.readyState == 4 && $class.status == 200) {
        status(0);
        initOpts(); // in case things have changed...
    }
}

var opts;

function status(turn_on)
{
    // from SMF
    var indicator = document.getElementById("status");
    if (indicator != null)
    {
        if (navigator.appName == "Microsoft Internet Explorer" && navigator.userAgent.indexOf("MSIE 7") == -1)
        {
            indicator.style.top = document.documentElement.scrollTop;
        }
        indicator.style.display = turn_on ? "block" : "none";
    }
}

function doPost(){
    status(1);
    postData=[];
    for (e in opts)
        postData=postData.concat([e+'='+opts[e]])
    ajax("/cgi-bin/hachoir.py",postData.join('&'),updateHTML);
}

function setOpt(s){
    opts[s]=document.getElementById('check_'+s).checked*1;
    saveOpts();
    doPost();
}

function getOpt(s, check){
    v=get_cookie(s);
    if (v)
    {
        v=v.replace(/"(.+)"/,"$1");
        opts[s]=v;
        if (check)
            document.getElementById('check_'+s).checked=(v=='1')?true:false;
    }
}

function saveOpts(){
    for(s in opts)
        set_cookie(s,opts[s],3600*24*365*10); // save for 10 years
}

function initOpts(){
    getOpt('hpath');
    getOpt('stream');
    getOpt('raw',true);
    getOpt('hex',true);
    getOpt('rel',true);
}

function doInit(){
    opts={'hpath':'/','stream':'0'};
    initOpts();
    doPost();
}

function goPath(s){
    paths=opts.hpath.split(':');
    paths[parseInt(opts.stream)]=s;
    opts.hpath=paths.join(':');
    doPost();
    saveOpts();
}

function addStream(spath){
    // set command, post, remove command from options
    opts.addStream=spath;
    doPost();
    delete opts.addStream;
    saveOpts();
}

function delStream(n){
    // set command, post, remove command from options
    opts.delStream=n.toString();
    doPost();
    delete opts.delStream;
    saveOpts();
}

function set_cookie( name, value, expires, path, domain, secure )
{
    // set time, it's in milliseconds
    var today = new Date();
    today.setTime( today.getTime() );

    /*
    if the expires variable is set, make the correct
    expires time, the current script below will set
    it for x number of days, to make it for hours,
    delete * 24, for minutes, delete * 60 * 24
    */
    if ( expires )
    {
        expires = expires * 1000;
    }
    var expires_date = new Date( today.getTime() + (expires) );

    document.cookie = name + "=" +escape( value ) +
    ( ( expires ) ? ";expires=" + expires_date.toGMTString() : "" ) +
    ( ( path ) ? ";path=" + path : "" ) +
    ( ( domain ) ? ";domain=" + domain : "" ) +
    ( ( secure ) ? ";secure" : "" );
}

// this function gets the cookie, if it exists
function get_cookie( name ) {
    var start = document.cookie.indexOf( name + "=" );
    var len = start + name.length + 1;
    if ( ( !start ) &&
    ( name != document.cookie.substring( 0, name.length ) ) )
    {
        return null;
    }
    if ( start == -1 ) return null;
    var end = document.cookie.indexOf( ";", len );
    if ( end == -1 ) end = document.cookie.length;
    return unescape( document.cookie.substring( len, end ) );
}

function delete_cookie ( cookie_name )
{
    var cookie_date = new Date ( );  // current date & time
    cookie_date.setTime ( cookie_date.getTime() - 1 );
    document.cookie = cookie_name += "=; expires=" + cookie_date.toGMTString();
}

