
function change_stream_visibility()
{
    if( document.stream.public.selectedIndex == 0 )
    {
        document.getElementById('a_pass').style.display = 'none';
    }
    else
    {
        document.getElementById('a_pass').style.display = 'block';
    }
}

function clear_comment(item, defm)
{
    if( item.value == trim(defm) )
    {
        item.value = '';
    }
}

function remove_comment(id)
{
    if( confirm('Do you really want to remove this comment?') )
    {
        window.location.href = '/comment?rm=' + id;
    }
}

function remove_report(id)
{
    if( confirm('Do you really want to remove this report?') )
    {
        window.location.href = '/admin/reports?rm=' + id;
    }
}

function remove_request(id)
{
    if( confirm('Do you really want to remove this request?') )
    {
        window.location.href = '/admin/requests?rm=' + id;
    }
}

function remove_stream(id)
{
    if( confirm('Do you really want to remove this stream?') )
    {
        window.location.href = '/admin/streams?rm=' + id;
    }
}

function select_pylinks_lens(lens)
{
    if(lens == 'text')
    {
        document.getElementById('pyl_default_lens').style.display = 'none';
        document.getElementById('pyl_text_lens').style.display = 'block';
        document.getElementById('btn_pyl_def_lens').setAttribute("class", "caca");
        document.getElementById('btn_pyl_txt_lens').setAttribute("class", "selected");
    }
    else
    {
        document.getElementById('pyl_default_lens').style.display = 'block';
        document.getElementById('pyl_text_lens').style.display = 'none';
        document.getElementById('btn_pyl_def_lens').setAttribute("class", "selected");
        document.getElementById('btn_pyl_txt_lens').setAttribute("class", "caca");
    }
}

function show_on_iframe(webname)
{
    if(webname == 'imgur')
    {
        document.getElementById('webservice').src = 'http://www.imgur.com';
        document.getElementById('webservice').height = '700px';
    }
    else if(webname == 'megaupload')
    {
        document.getElementById('webservice').src = 'http://www.megaupload.com';
        document.getElementById('webservice').height = '700px';
    }
}

function trim(s)
{
    return s.replace(/^\s*|\s*$/g,'');
}

