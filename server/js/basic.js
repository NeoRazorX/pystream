function set_public_stream()
{
    if( document.stream.public[0].checked )
    {
        document.stream.password.value = '';
        document.stream.password.disabled = true;
    }
}

function set_private_stream()
{
    if( document.stream.public[1].checked )
    {
        document.stream.password.disabled = false;
    }
}

function remove_stream(id)
{
    if( confirm('Do you really want to remove this stream?') )
    {
        window.location.href = '/admin/streams?rm=' + id;
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

function this_is_alpha()
{
    alert("Pystream is in alpha state, is not ready yet!\nTry again tomorrow...\nOr mail me: admin@pystream.com");
}
