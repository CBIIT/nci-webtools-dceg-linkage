function submitForm() {
    console.log('button clicked')
    var first = $('#first').val();
    var second = $('#second').val();
    var json = {
        first: first,
        second: second,
    }
    
	var url = "../LDlinkRest/demoapp/add";
	var ajaxRequest = $.ajax({
		type : 'POST',
		url : url,
		data : json,
		contentType : 'application/json',
        success : function(result) {
            jQuery("#results").html(result); 
        },error : function(result){
            console.log(result);
        }
	});
    
    console.log('JSON',json);

}

