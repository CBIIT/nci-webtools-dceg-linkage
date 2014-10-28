$( document ).ready(function() {
		console.log( "ready!" );
		$( "#calculate-button" ).click(function() {
			$("#results-container").load('output.json');
		});
		$('#population-codes').multiselect({
			enableClickableOptGroups: true, 
			buttonWidth: '400px',
				dropRight: true
		});

});
