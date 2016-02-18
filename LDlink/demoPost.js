function submitForm() {
    console.log('button clicked')
    var first = $('#first').val();
    var second = $('#second').val();
    var json = {
        first: first,
        second: second,
    }
    
	var url = "/demoapp/add";
	var ajaxRequest = $.ajax({
		type : 'POST',
		url : url,
		data : json,
		contentType : 'application/json' // JSON
	});
    
    console.log('JSON',json);

}

