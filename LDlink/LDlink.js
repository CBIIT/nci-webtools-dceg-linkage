var restService = {
  protocol : 'http',
  hostname : document.location.hostname,
  fqn : "nci.nih.gov",
  port : 9090,
  route : "LDlinkRest"
}

var restServerUrl = restService.protocol + "://" + restService.hostname + "/"
    + restService.route;

var populations={
	AFR:{
		fullName:"African",
		subPopulations:
		{YRI:"Yoruba in Ibadan, Nigera",LWK:" Luhya in Webuye, Kenya",GWD:" Gambian in Western Gambia",MSL:"  Mende in Sierra Leone",ESN:"  Esan in Nigera",ASW:" Americans of African Ancestry in SW USA",ACB:"  African Carribbeans in Barbados"}},AMR:{fullName:"Ad Mixed American",subPopulations:{MXL:"  Mexican Ancestry from Los Angeles, USA",PUR:" Puerto Ricans from Puerto Rico",CLM:" Colombians from Medellin, Colombia",PEL:" Peruvians from Lima, Peru"}},EAS:{fullName:"East Asian",subPopulations:{CHB:" Han Chinese in Bejing, China",JPT:" Japanese in Tokyo, Japan",CHS:" Southern Han Chinese",CDX:" Chinese Dai in Xishuangbanna, China",KHV:"  Kinh in Ho Chi Minh City, Vietnam"}},EUR:{fullName:"European",subPopulations:{CEU:" Utah Residents from North and West Europe",TSI:"  Toscani in Italia",FIN:"  Finnish in Finland",GBR:" British in England and Scotland",IBS:"  Iberian population in Spain"}},SAS:{fullName:"South Asian",subPopulations:{GIH:"  Gujarati Indian from Houston, Texas",PJL:"  Punjabi from Lahore, Pakistan",BEB:"  Bengali from Bangladesh",STU:"  Sri Lankan Tamil from the UK",ITU:" Indian Telugu from the UK"}}};

var ldPairData={corr_alleles:["rs2720460(A) allele is correlated with rs11733615(C) allele","rs2720460(G) allele is correlated with rs11733615(T) allele"],haplotypes:{hap1:{alleles:"AC",count:"155",frequency:"0.686"},hap2:{alleles:"GC",count:"40",frequency:"0.177"},hap3:{alleles:"GT",count:"29",frequency:"0.128"},hap4:{alleles:"AT",count:"2",frequency:"0.009"}},snp1:{allele_1:{allele:"A",count:"157",frequency:"0.695"},allele_2:{allele:"G",count:"69",frequency:"0.305"},coord:"chr4:104054686",rsnum:"rs2720460"},snp2:{allele_1:{allele:"C",count:"195",frequency:"0.863"},allele_2:{allele:"T",count:"31",frequency:"0.137"},coord:"chr4:104157164",rsnum:"rs11733615"},statistics:{chisq:"67.271",d_prime:"0.9071",p:"0.0",r2:"0.2977"},two_by_two:{cells:{c11:"155",c12:"2",c21:"40",c22:"29"},total:"old - 227"}};
var ldProxyData = {top10:  [{"Alleles":"newProxy","Coord":"chr12:126891966","Corr_Alleles":"G-G,A-A","Dist":986,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs7957025","RegulomeDB":"5"},{"Alleles":"(A/G)","Coord":"chr12:126888368","Corr_Alleles":"G-A,A-G","Dist":-2612,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs10847146","RegulomeDB":"5"},{"Alleles":"(T/A)","Coord":"chr12:126894660","Corr_Alleles":"G-T,A-A","Dist":3680,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs11058634","RegulomeDB":"7"},{"Alleles":"(G/C)","Coord":"chr12:126887133","Corr_Alleles":"G-G,A-C","Dist":-3847,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs11058630","RegulomeDB":"6"},{"Alleles":"(G/A)","Coord":"chr12:126895215","Corr_Alleles":"G-G,A-A","Dist":4235,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs11058636","RegulomeDB":"7"},{"Alleles":"(G/T)","Coord":"chr12:126895996","Corr_Alleles":"G-G,A-T","Dist":5016,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs7972985","RegulomeDB":"6"},{"Alleles":"(C/T)","Coord":"chr12:126885179","Corr_Alleles":"G-C,A-T","Dist":-5801,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs61942997","RegulomeDB":"5"},{"Alleles":"(A/G)","Coord":"chr12:126884784","Corr_Alleles":"G-A,A-G","Dist":-6196,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs12579545","RegulomeDB":"7"},{"Alleles":"(G/A)","Coord":"chr12:126898373","Corr_Alleles":"G-G,A-A","Dist":7393,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs7132131","RegulomeDB":"7"}]};
var ldhapData = {"footer":[{"Count":127,"Frequency":0.588,"Haplotype":"GCATGGCGTTGGGG"},{"Count":40,"Frequency":0.1852,"Haplotype":"GGGGAGCGTTGGGG"},{"Count":23,"Frequency":0.1065,"Haplotype":"GCGGAGCGTTGGGG"},{"Count":11,"Frequency":0.0509,"Haplotype":"TGGGAGCGTTGGGG"},{"Count":8,"Frequency":0.037,"Haplotype":"GCATAGCGTTGGGG"},{"Count":7,"Frequency":0.0324,"Haplotype":"TGGGGATAGCAAAG"}],"rows":[{"Alleles":"G=0.917, T=0.083","Coord":"chr4:104050980","RS":"rs2720457","Haplotypes":["G","G","G","T","G","T"]},{"Alleles":"C=0.732, G=0.269","Coord":"chr4:104052963","RS":"rs2720458","Haplotypes":["C","G","C","G","C","G"]},{"Alleles":"A=0.625, G=0.375","Coord":"chr4:104055748","RS":"rs2720461","Haplotypes":["A","G","G","G","A","G"]},{"Alleles":"T=0.625, G=0.375","Coord":"chr4:104056210","RS":"rs2720462","Haplotypes":["T","G","G","G","T","G"]},{"Alleles":"G=0.62, A=0.38","Coord":"chr4:104052068","RS":"rs7661201","Haplotypes":["G","A","A","A","A","G"]},{"Alleles":"G=0.968, A=0.032","Coord":"chr4:104055722","RS":"rs2623063","Haplotypes":["G","G","G","G","G","A"]},{"Alleles":"C=0.968, T=0.032","Coord":"chr4:104057121","RS":"rs2623062","Haplotypes":["C","C","C","C","C","T"]},{"Alleles":"G=0.968, A=0.032","Coord":"chr4:104057248","RS":"rs2720463","Haplotypes":["G","G","G","G","G","A"]},{"Alleles":"T=0.968, G=0.032","Coord":"chr4:104057887","RS":"rs2711901","Haplotypes":["T","T","T","T","T","G"]},{"Alleles":"T=0.968, C=0.032","Coord":"chr4:104051132","RS":"rs2623082","Haplotypes":["T","T","T","T","T","C"]},{"Alleles":"G=0.968, A=0.032","Coord":"chr4:104058596","RS":"rs2711900","Haplotypes":["G","G","G","G","G","A"]},{"Alleles":"G=0.968, A=0.032","Coord":"chr4:104050510","RS":"rs2720456","Haplotypes":["G","G","G","G","G","A"]},{"Alleles":"G=0.968, A=0.032","Coord":"chr4:104050326","RS":"rs2720455","Haplotypes":["G","G","G","G","G","A"]},{"Alleles":"G=1.0, A=0.0","Coord":"chr4:104059542","RS":"rs2243682","Haplotypes":["G","G","G","G","G","G"]}]};

//Map knockout models to a sample json data
var ldproxyModel = ko.mapping.fromJS(ldProxyData);
var ldpairModel = ko.mapping.fromJS(ldPairData);
var ldhapModel = ko.mapping.fromJS(ldhapData);

$(document).ready(function() {

	var modules = ["ldhap", "ldmatrix", "ldpair", "ldproxy"];

	// Apply Bindings
	ko.applyBindings(ldpairModel, document.getElementById('ldpair-results-container'));
	ko.applyBindings(ldproxyModel, document.getElementById('ldproxy-results-container'));
	ko.applyBindings(ldhapModel, document.getElementById('ldhap-results-container'));

	$.each(modules, function(key, id) {
		buildPopulationDropdown(id+"-population-codes");
		$("#"+id+"-results-container").hide();
		$('#'+id+'-message').hide();
		$('#'+id+'-message-warning').hide();
	});

	/*
	$('.tab-content').on('click',
		"a[class|='btn btn-default calculate']", function(e) {
		calculate(e);
	});

	$('.tab-content').on('click',
		"button[class|='btn btn-default calculate']", function(e) {
		calculate(e);
	});
	
	*/
	
	$('.ldlinkForm').on('submit', function (e) {
		calculate(e);
	});

	// Add file select file listener
	$('.btn-file :file').on('fileselect', function(event, numFiles, label) {
		populateTextArea(event, numFiles, label);
		var input = $(this).parents('.input-group').find(':text'),
		log = numFiles > 1 ? numFiles + ' files selected' : label;
		if (input.length) {
			input.val(log);
		} else {
			if (log)
				alert(log);
		}
	});

	$( "body" ).keypress(function(e) {
		//Look for a return value
		var code = e.keyCode || e.which;
		if(code == 13) { //User pressed return key
			//make sure focus is not in a textarea.  If so ignore.
			var event_id = e.target.id;
			//Skip if you can't get event_id
			if(event_id === "") {

			} else {
				//Skip if user is editing TEXTAREA
				var tag_name = $("#"+event_id).get(0).tagName;
				if(tag_name == "TEXTAREA") {
					return;
				}
			}

			console.log("********");
			console.log("event_id");
			console.log(event_id);
			console.log('typeof event_id');
			console.log(typeof event_id);


			console.log('tag_name');
			console.log(tag_name);
			var active_tab = $("div.tab-pane.active").attr('id');
			var id = active_tab.split("-");
			if(id.length == 2) { //Check to make sure we are on a calculate tab
				initCalculate(id[0]);
				updateData(id[0]);
			}
		}
	});

	//addValidators();

});

//Set file support trigger
$(document).on('change', '.btn-file :file', function() {
	var input = $(this), numFiles = input.get(0).files ? input.get(0).files.length : 1, label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
	input.trigger('fileselect', [ numFiles, label ]);
});

function populateTextArea(event, numFiles, label) {
  id = event.target.id;
  if(window.FileReader) {

    var input = event.target;
    var reader = new FileReader();
    reader.onload = function(){
      var text = reader.result;
      $('#'+id+'-snp-numbers').val(text);
    };
    reader.readAsText(input.files[0]);
  } else {
    alert('FileReader not supported');
    return;
  }
}

function calculate(e) {
	var formId = e.target.id;
	e.preventDefault();
//	var firstClick = $('#'+id+'-results-container').hasClass( "hidden" );

	//strip out "Form" from id
	var id=formId.slice(0, formId.length-4);

	initCalculate(id);
	updateData(id);
}
function initCalculate(id) {
	$('#'+id+'-results-container').hide();
	$('#'+id+'-message').hide();
	$('#'+id+'-message-warning').hide();
}

function updateData(id) {
	//Make this generic...
	//ie. prepare url and post data.
	//Get data...
	console.log("updateData("+id+")");

	switch (id) {
	case 'ldpair':
					updateLDpair();
		break;
	case 'ldproxy':
      $('#'+id+'-progress-container').show();
      //ko.mapping.fromJS(newProxy4, ldproxyModel);
      updateLDproxy();
		break;
	case 'ldmatrix':
      //console.log($('#ldmatrix-form').serialize());
      updateLDmatrix();
		break;
	case 'ldhap':
      $('#'+id+'-results-container').show();
      updateLDhap();
		break;
	}

}

function updateLDhap() {
  var id = "ldhap";

  var $btn = $('#'+id).button('loading');
  var snps = $('#'+id+'-file-snp-numbers').val();
  var population = $('#'+id+'-population-codes').val();

  var ldInputs = {
    snps: snps,
    pop : population.join("+"),
    reference : Math.floor(Math.random() * (99999 - 10000 + 1))
  };
  console.log('ldInputs');
  console.dir(ldInputs);

  var url = restServerUrl + "/ldhap";
  var ajaxRequest = $.ajax({
    type : 'GET',
    url : url,
    data : ldInputs
  });

  ajaxRequest.success(function(data) {
		if (displayError(id, data) == false) {
      $('#'+id+'-results-container').show();
      var ldhapTable = formatLDhapData($.parseJSON(data));
      $('#ldhap-haplotypes-column').attr('colspan', ldhapTable.footer.length);
      ko.mapping.fromJS(ldhapTable, ldhapModel);
      addLDHapHyperLinks(ldInputs.reference, ldhapTable);
		}
	});
  ajaxRequest.fail(function(jqXHR, textStatus) {
    console.log("header: " + jqXHR + "\n" + "Status: " + textStatus
        + "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
    //alert('Communication problem: ' + textStatus);
    // ERROR
    message = 'Service Unavailable: ' + textStatus+"<br>";
    message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

    $('#'+id+'-message').show();
    $('#'+id+'-message-content').empty().append(message);
    $('#'+id+'-progress').hide();
  });
  ajaxRequest.always(function() {
    $btn.button('reset');
  });

}

function formatLDhapData(data) {

  console.log('ldhap data');
  console.dir(data);

  var haplotypes = data.haplotypes;
  var snps = data.snps;

  var ldhapTable = {footer:[], rows:[]};

  //Convert haplotypes to footer
  for (key in haplotypes) {
    console.log(key);
    console.dir(haplotypes[key]);
    var obj = {
      Count: haplotypes[key].Count,
      Frequency: haplotypes[key].Frequency,
      Haplotype: haplotypes[key].Haplotype
    };
    // Add Haplotypes with a frequency of 1% or greater.
  	if(haplotypes[key].Frequency*100>1) {
		ldhapTable.footer.push(obj);
	}
  }
  //Convert snps to rows.
  for (key in snps) {
    var obj = {
      Alleles: snps[key].Alleles,
      Coord: snps[key].Coord,
      RS: snps[key].RS,
      Haplotypes: []
    };
    ldhapTable.rows.push(obj);
  }
  //Add haplotypesHTML
  $.each(ldhapTable.rows, function(index, value){
    //Get all the haplotypes in pivot order
    $.each(ldhapTable.footer, function(index2, value2){
        value.Haplotypes[index2] = value2.Haplotype.substr(index, 1);
    });
  });

  console.log('ldhapTable');
  console.dir(ldhapTable);
  var obj = {
    out_final: ldhapTable
  }
  console.dir(obj);

  return ldhapTable;
}

function updateLDmatrix() {
  var id = "ldmatrix";

  var $btn = $('#'+id).button('loading');

  var snps = $('#'+id+'-file-snp-numbers').val();
  var population = $('#'+id+'-population-codes').val();
  var ldmatrixInputs = {
    snps: snps,
    pop : population.join("+"),
    reference : Math.floor(Math.random() * (99999 - 10000 + 1))
  };
  console.log('ldmatrixInputs');
  console.dir(ldmatrixInputs);

  var url = restServerUrl + "/ldmatrix";
  var ajaxRequest = $.ajax({
    type : 'GET',
    url : url,
    data : ldmatrixInputs
  });

  ajaxRequest.success(function(data) {
		if (displayError(id, data) == false) {
      $('#ldmatrix-bokeh-graph').empty().append(data);
      $('#'+id+'-progress-container').hide();
      $('#'+id+'-results-container').show();
      addLDMatrixHyperLinks(ldmatrixInputs.reference);
    }
  });
  ajaxRequest.fail(function(jqXHR, textStatus) {
    console.log("header: " + jqXHR + "\n" + "Status: " + textStatus
        + "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
    //alert('Communication problem: ' + textStatus);
    // ERROR
    message = 'Service Unavailable: ' + textStatus+"<br>";
    message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

    $('#'+id+'-message').show();
    $('#'+id+'-message-content').empty().append(message);
    $('#'+id+'-progress').hide();
  });
  ajaxRequest.always(function() {
    $btn.button('reset');
  });

}

function addLDMatrixHyperLinks(request) {
  $('#ldmatrix-DPrime').attr('href','tmp/d_prime_'+request+'.txt');
  $('#ldmatrix-R2').attr('href','tmp/r2_'+request+'.txt');
}

function updateLDproxyProgressBar(id, seconds) {

  	var milliseconds = seconds * 1000;
  	// Divide number of milliseconds to get 100 to get 100 updates
  	var delay = milliseconds / 100;

	$('#'+id+'-progress').show();
    var progressBar = $('#ldproxy-progress-bar');
    width = 0;

    progressBar.width(width);

    var interval = setInterval(function() {
        width += 1;
        progressBar.css('width', width + '%').attr('aria-valuenow', width.toString()+'%');
        progressBar.html('<span>'+width.toString()+'% Complete</span>');
        if (width >= 100) {
            clearInterval(interval);
            return;
        }
    }, delay);
}

function createPopulationDropdown(id) {

	$('#' + id + '-population-codes').multiselect({
		enableClickableOptGroups : true,
		buttonWidth : '180px',
		maxHeight : 500,
		includeSelectAllOption : true,
		dropRight : true,
		allSelectedText : 'All Populations',
		nonSelectedText : 'Select Population',
		numberDisplayed : 4,
		selectAllText : 'All Populations',

		// buttonClass: 'btn btn-link',
		buttonText : function(options, select) {
			if (options.length === 0) {
				return '<span class="pull-left">'
							+this.nonSelectedText
						+'</span>'
						+ ' <b class="caret"></b>';
			} else if (options.length == $('option', $(select)).length) {
				return '<span class="pull-left">'
							+this.nonSelectedText
						+'</span>'
						+ ' <b class="caret"></b>';
			} else if (options.length > this.numberDisplayed) {
				return '<span class="badge pull-left">' + options.length
						+ '</span> ' + this.nSelectedText
						+ ' <b class="caret"></b>';
			} else {
				var selected = '';
				options.each(function() {
					// var label = $(this).attr('label') :
					// $(this).html();
					selected += $(this).val() + '+';
				});

				return selected.substr(0, selected.length - 1)
						+ ' <b class="caret"></b>';
			}
		},
		buttonTitle : function(options, select) {
			if (options.length === 0) {
				return this.nonSelectedText;
			} else {
				var selected = '';
				options.each(function() {
					selected += $(this).text() + '\n';
				});
				return selected;
			}
		}
	});
}

function updateLDproxy() {
  var id = "ldproxy";

  var $btn = $('#'+id).button('loading');

  var population = $('#ldproxy-population-codes').val();
  var ldproxyInputs = {
    snp : $('#ldproxy-snp').val(),
    pop : population.join("+"),
    reference : Math.floor(Math.random() * (99999 - 10000 + 1))
  };

  console.dir(ldproxyInputs);

  $('#ldproxy-results-link').attr('href', 'tmp/proxy'+ldproxyInputs.reference+'.txt');
  $('#ldproxy-progress-bar').attr('aria-valuenow', "0");

		//
		//Determine caclulation time.
		//Wait 1.5 seconds for pops file to be created.
		//

	setTimeout(function(){
			//Determine seconds...
		var url = 'tmp/pops_'+ldproxyInputs.reference+'.txt';
		var base_calculation_time = 20; //seconds
		var bokeh_load_time = 8; //seconds
		var sample_multiplier = 0.0256; //seconds per sample

		var seconds = 0;
		var ajaxRequest = $.ajax({
			type : "GET",
			url : url
	});

	ajaxRequest.success(function(data) {
			console.log("Estimate for number of seconds");
			console.info(seconds);
			sample_count = data.split("\n").length;
			console.log("sample_count = "+ sample_count);
			seconds = (sample_multiplier * sample_count)
					+ base_calculation_time + bokeh_load_time;
			console.log("Total Seconds =");
			console.log(seconds);
			updateLDproxyProgressBar(id, seconds);
	});
		ajaxRequest.fail(function(jqXHR, textStatus) {
			//Create a linear guess based on
			// One (1) population take 30 seconds
			// All (26) populations take 93 seconds.
			//Get populations list length...
			var population = $('#ldproxy-population-codes').val();
			console.log(population);
			//Get number of populations selected min 1 thru max 30
			var pop_selected = population.length;
			console.log("populations selected");
			console.log(pop_selected);
			// Backup estimeate30 + (2.42 * x) = seconds
			var backup_estimate_multiplier =2.5;
			seconds = (backup_estimate_multiplier * pop_selected)
					+ base_calculation_time + bokeh_load_time;
			console.log("Using Backup Estimate for number of seconds");
			console.info(seconds);
			updateLDproxyProgressBar(id, seconds);

		});

		ajaxRequest.always(function() {
			console.log('AJAX call done for LDProxy estimate');
		});

	}, 1500);

  var url = restServerUrl + "/ldproxy";
  var ajaxRequest = $.ajax({
    type : "GET",
    url : url,
    data : ldproxyInputs
  });

  ajaxRequest.success(function(data) {
    $('#'+id+'-progress-container').hide();
		if (displayError(id, data) == false) {
      $('#ldproxy-bokeh-graph').empty().append(data);
      $('#'+id+'-results-container').show();
      getLDProxyResults('proxy'+ldproxyInputs.reference+'.json');
    }
  });
  ajaxRequest.fail(function(jqXHR, textStatus) {
    console.log("header: " + jqXHR + "\n" + "Status: " + textStatus
        + "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
    //alert('Communication problem: ' + textStatus);
    // ERROR
    message = 'Service Unavailable: ' + textStatus+"<br>";
    message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

    $('#'+id+'-message').show();
    $('#'+id+'-message-content').empty().append(message);
    $('#'+id+'-progress').hide();
  });
  ajaxRequest.always(function() {
    $btn.button('reset');
  });

}

function getLDProxyResults(jsonfile) {

  var id = "proxy";
  var url = "tmp/"+jsonfile;
  var ajaxRequest = $.ajax({
    type : "GET",
    url : url,
    format: "json"
  });

  ajaxRequest.success(function(data) {
    ko.mapping.fromJS(data, ldproxyModel);
	  addLDproxyHyperLinks(data);
  });
  ajaxRequest.fail(function(jqXHR, textStatus) {
    //alert('Fail');
    console.log("header: " + jqXHR + "\n" + "Status: " + textStatus
        + "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
    message = 'Service Unavailable: ' + textStatus+"<br>";
    message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

    $('#'+id+'-message').show();
    $('#'+id+'-message-content').empty().append(message);
    $('#'+id+'-progress').hide();
  });
  ajaxRequest.always(function() {
  });
}

function updateLDpair() {
	var id = 'ldpair';
  var $btn = $('#'+id).button('loading');

	var population = $('#ldpair-population-codes').val();
	console.log("LD Pair");
	console.log('population');
	console.dir(population);
	var ldpairInputs = {
		snp1 : $('#ldpair-snp1').val(),
		snp2 : $('#ldpair-snp2').val(),
		pop : population.join("+"),
		reference : "ref" + Math.floor(Math.random() * (99999 - 10000 + 1))
				+ 10000
	};

	var url = restServerUrl + "/ldpair";

	var ajaxRequest = $.ajax({
		type : "GET",
		url : url,
		data : ldpairInputs,
		contentType : 'application/json' // JSON
	});

	ajaxRequest.success(function(data) {
		if (displayError(id, data) == false) {
      ko.mapping.fromJS(data, ldpairModel);
      $('#'+id+'-results-container').show();
      addLDpairHyperLinks(data);
		}
	});
	ajaxRequest.fail(function(jqXHR, textStatus) {
		console.log("header: " + jqXHR + "\n" + "Status: " + textStatus
				+ "\n\nMake sure Flask Python server is available.");
		//alert('Communication problem: ' + textStatus);
    // ERROR
    $('#'+id+'-message').show();
    $('#'+id+'-message-content').empty().append('Communication problem: ' + textStatus+"<br>Make sure Plask Python server is available.");
	});
	ajaxRequest.always(function() {
    $btn.button('reset');
	});
}

function displayError(id, data) {
	// Display error or warning if available.
		var error = false;
		if(data.warning) {
      $('#'+id+'-message-warning').show();
      $('#'+id+'-message-warning-content').empty().append(data.warning);
    }

		if (data.error) {
      // ERROR
      $('#'+id+'-message').show();
      $('#'+id+'-message-content').empty().append(data.error);
      error = true;
		}
		return error;
}

function addLDHapHyperLinks(request, ldhapTable) {
		$('#ldhap-snps').attr('href','tmp/snps_'+request+'.txt');
		$('#ldhap-haplotypes').attr('href','tmp/haplotypes_'+request+'.txt');

    var server;
    var params = {};
    var rs_number;
    var url;
    server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';

    $.each(ldhapTable.rows, function( index, value ) {
				console.log( index + ": " + value );
				//Create RSnumber link (Cluster Report)
				server = 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi';
				// snp1-rsum
				rs_number = value.RS.substring(2);
				params = {rs: rs_number};
				url = server+"?"+$.param(params);
				$('#RSnumber_hap_'+index+' a:first-child').attr('href', url);

				//Create Coord link ()
				server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';
				positions = value.Coord.split(":");
				chr = positions[0];
				mid_value = parseInt(positions[1]);
				offset =250;
				range = (mid_value-offset)+"-"+(mid_value+offset);
				position = chr+":"+range;
				rs_number = value.RS;
				params = {
						position: position,
						snp141: 'pack',
						'hgFind.matches' : rs_number
				};
				url = server+"?"+$.param(params);
				$('#Coord_hap_'+index+' a:first-child').attr('href', url);
		});

}

function addLDproxyHyperLinks(data) {
    var server;
    var params = {};
    var rs_number;
    var url;
    //Find the coord of the rs number
    //
    // Cluster Report:
    //
    server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';
    //http://genome.ucsc.edu/cgi-bin/hgTracks?
    //position=chr4:103554686-104554686
    //&snp141=pack
    //&hgFind.matches=rs2720460
    // snp1-coord

    //
    // Genome Browser:
    //

    var positions = data.query_snp.Coord.split(":");
    var chr = positions[0];
    var mid_value = parseInt(positions[1]);
    var offset =500000;
    var range = (mid_value-offset)+"-"+(mid_value+offset);
    var position = chr+":"+range;
    rs_number = data.query_snp.RS;
    params = {
      position: position,
      snp141: 'pack',
      'hgFind.matches' : rs_number
    };
		url = server+"?"+$.param(params);
		$('#ldproxy-link').attr('href', url);
/*

RS number=rs2720460
Position=chr4:104054686
Pos_minus_250bp=104054436
Pos_plus_250bp=104054936

Add three links to the following columns in the top 10 proxy table:

RS Number Column links: (Cluster Report)
http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=2720460

Coord Column links:
http://genome.ucsc.edu/cgi-bin/hgTracks?position=chr4:104054436-104054936&snp141=pack&hgFind.matches=rs2720460

RegulomeDB links:
http://www.regulomedb.org/snp/chr4/104054685

## Notice the minus one base pair for the RegulomeDB coordinate in the link. They use a 0 based system for coordinates and not a one based system like our coordinates.
*/
		//Add links to the top10 table
	$.each(data.top10, function( index, value ) {

		//Create RSnumber link (Cluster Report)
		server = 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi';
		// snp1-rsum
		rs_number = value.RS.substring(2);
		params = {rs: rs_number};
		url = server+"?"+$.param(params);
		$('#RSnumber_'+index+' a:first-child').attr('href', url);

		//Create Coord link ()
		server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';
		positions = value.Coord.split(":");
		chr = positions[0];
		mid_value = parseInt(positions[1]);
		offset =250;
		range = (mid_value-offset)+"-"+(mid_value+offset);
		position = chr+":"+range;
		rs_number = value.RS;
		params = {
				position: position,
				snp141: 'pack',
				'hgFind.matches' : rs_number
		};
		url = server+"?"+$.param(params);
		$('#Coord_'+index+' a:first-child').attr('href', url);

		//Create RegulomeDB links
		server = 'http://www.regulomedb.org/snp';
		positions = value.Coord.split(":");
		chr = positions[0];
		mid_value = parseInt(positions[1]);
		zero_base = mid_value-1;

		url = server+"/"+chr+"/"+zero_base;
		$('#RegulomeDB_'+index+' a:first-child').attr('href', url);


	});

}

function addLDpairHyperLinks(data) {
  // Add snp1-rsum to
    var server;
    var params = {};
    var rs_number;
    var url;
    //
    // Cluster Report:
    //
    server = 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi';
    // snp1-rsum
    rs_number = data.snp1.rsnum.substring(2);
    params = {rs: rs_number};
    url = server+"?"+$.param(params);
    $('#snp1-rsnum').attr('href', url)
    // snp2-rsum
    rs_number = data.snp2.rsnum.substring(2);
    params = {rs: rs_number};
    url = server+"?"+$.param(params);
    $('#snp2-rsnum').attr('href', url)
    //
    // Genome Browser:
    //
    server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';
    // snp1-coord
    var positions = data.snp1.coord.split(":");
    var chr = positions[0];
    var mid_value = parseInt(positions[1]);
    var offset =250;
    var range = (mid_value-offset)+"-"+(mid_value+offset);
    var position = chr+":"+range;
    rs_number = data.snp1.rsnum;
    params = {
      position: position,
      snp141: 'pack',
      'hgFind.matches' : rs_number
    };
    url = server+"?"+$.param(params);
    $('#snp1-coord').attr('href', url)
    // snp2-coord
    positions = data.snp2.coord.split(":");
    chr = positions[0];
    mid_value = parseInt(positions[1]);
    offset =250;
    range = (mid_value-offset)+"-"+(mid_value+offset);
    position = chr+":"+range;
    rs_number = data.snp2.rsnum;
    params = {
      position: position,
      snp141: 'pack',
      'hgFind.matches' : rs_number
    };
    url = server+"?"+$.param(params);
    $('#snp2-coord').attr('href', url);

}

function buildPopulationDropdown(elementId) {
  var htmlText = "";
  var htmlText1 = "<optgroup value='ABBREV' label='(ABBREV) FULLNAME'>\n";
  var htmlText2 = "<option value='ABBREV'>(ABBREV) DETAIL </option>\n";
  for ( var popAbbrev in populations) {
    var population = populations[popAbbrev];
    htmlText += htmlText1.replace(/ABBREV/g, popAbbrev).replace("FULLNAME", population.fullName);
    for ( var subPopAbbrev in population.subPopulations) {
      var subDetail = population.subPopulations[subPopAbbrev];
      htmlText += htmlText2.replace(/ABBREV/g, subPopAbbrev).replace("DETAIL", subDetail);
    }
    htmlText += "</optgroup>\n";
  }
  $('#' + elementId).html(htmlText);

  $('#' + elementId)
      .multiselect(
          {
            enableClickableOptGroups : true,
            buttonWidth : '180px',
            maxHeight : 500,
            buttonClass: 'btn btn-default btn-ldlink-multiselect',
            includeSelectAllOption : true,
            dropRight : false,
            allSelectedText : 'All Populations',
            nonSelectedText : 'Select Population',
            numberDisplayed : 4,
            selectAllText : ' (ALL) All Populations',

            // buttonClass: 'btn btn-link',
            buttonText : function(options, select) {
              if (options.length === 0) {
                return this.nonSelectedText
                    + '<span class="caret"></span>';
              } else if (options.length == $('option', $(select)).length) {
                return this.allSelectedText
                    + '<span class="caret"></span>';
              } else if (options.length > this.numberDisplayed) {
                return '<span class="badge">' + options.length
                    + '</span> ' + this.nSelectedText
                    + '<span class="caret"></span>';
              } else {
                var selected = '';
                options.each(function() {
                  // var label = $(this).attr('label') :
                  // $(this).html();
                  selected += $(this).val() + '+';
                });

                return selected.substr(0, selected.length - 1)
                    + ' <b class="caret"></b>';
              }
            },
            buttonTitle : function(options, select) {
              if (options.length === 0) {
                return this.nonSelectedText;
              } else {
                var selected = '';
                options.each(function() {
                  selected += $(this).text() + '\n';
                });
                return selected;
              }
            }
          });
}

function addValidators() {
		//Add validators

		// LDHAP FORM
    $('#ldhapForm').find('[name="populations"]')
            .multiselect({
                onChange: function(element, checked) {
                    $('#ldhapForm').bootstrapValidator('revalidateField', 'populations');
                }
            }).end()
      .bootstrapValidator({
				excluded: ':disabled',
        feedbackIcons: {
            valid: 'fa  fa-check',
            invalid: 'fa  fa-close',
            validating: 'fa fa-refresh'
        },
        fields: {
            snp_textbox: {
            	selector: '.snp_textbox',
                    validators: {
                        notEmpty: {
                            message: 'The RS Number is required and cannot be empty'
                        },
                        regexp: {
                        		regexp: /^rs\d/i,
                        		message: 'Enter valid RS numbers'
                    		}
            			}
            },
            populations: {
                validators: {
                    callback: {
                        message: 'Please choose at least one population',
                        callback: function(value, validator, $field) {
                            // Get the selected options
                            var options = validator.getFieldElements('populations').val();
                            console.log('Options');
                            console.log(console);
                            return (options != null && options.length >= 1);
                        }
                    }
                }
            }
        }
    });


		// LDMATRIX FORM
    $('#ldmatrixForm').find('[name="populations"]')
            .multiselect({
                onChange: function(element, checked) {
                    $('#ldmatrixForm').bootstrapValidator('revalidateField', 'populations');
                }
            }).end()
      .bootstrapValidator({
				excluded: ':disabled',
        feedbackIcons: {
            valid: 'fa  fa-check',
            invalid: 'fa  fa-close',
            validating: 'fa fa-refresh'
        },
        fields: {
            snp_textbox: {
            	selector: '.snp_textbox',
                    validators: {
                        notEmpty: {
                            message: 'The RS Number is required and cannot be empty'
                        },
                        regexp: {
                        		regexp: /^rs\d/i,
                        		message: 'Enter valid RS numbers'
                    		}
            			}
            },
            populations: {
                validators: {
                    callback: {
                        message: 'Please choose at least one population',
                        callback: function(value, validator, $field) {
                            // Get the selected options
                            var options = validator.getFieldElements('populations').val();
                            console.log('Options');
                            console.log(console);
                            return (options != null && options.length >= 1);
                        }
                    }
                }
            }
        }
    });

		// LDPAIR FORM
    $('#ldpairForm').find('[name="populations"]')
            .multiselect({
                onChange: function(element, checked) {
                	console.log("GOT HERE");
                    $('#ldpairForm').bootstrapValidator('revalidateField', 'populations');
                }
            })
            .end()
      .bootstrapValidator({
				excluded: ':disabled',
        feedbackIcons: {
            valid: 'fa  fa-check',
            invalid: 'fa  fa-close',
            validating: 'fa fa-refresh'
        },
        fields: {
            snp: {
            	selector: '.snp',
                    validators: {
                        notEmpty: {
                            message: 'The RS Number is required and cannot be empty'
                        },
                        regexp: {
                        		regexp: /^rs\d+$/i,
                        		message: 'Enter a valid RS number'
                    		}
            			}
            },
            populations: {
                validators: {
                    callback: {
                        message: 'Please choose at least one population',
                        callback: function(value, validator, $field) {
                            // Get the selected options
                            var options = validator.getFieldElements('populations').val();
                            console.log('Options');
                            console.log(console);

                            return (options != null && options.length >= 1);
                        }
                    }
                }
            }
        }
    });

		// LDPROX FORM
    $('#ldproxyForm').find('[name="populations"]')
            .multiselect({
                onChange: function(element, checked) {
                    $('#ldproxyForm').bootstrapValidator('revalidateField', 'populations');
                }
            }).end()
      .bootstrapValidator({
				excluded: ':disabled',
        feedbackIcons: {
            valid: 'fa  fa-check',
            invalid: 'fa  fa-close',
            validating: 'fa fa-refresh'
        },
        fields: {
            snp: {
            	selector: '.snp',
                    validators: {
                        notEmpty: {
                            message: 'The RS Number is required and cannot be empty'
                        },
                        regexp: {
                        		regexp: /^rs\d+$/i,
                        		message: 'Enter a valid RS number'
                    		}
            			}
            },
            populations: {
                validators: {
                    callback: {
                        message: 'Please choose at least one population',
                        callback: function(value, validator, $field) {
                            // Get the selected options
                            var options = validator.getFieldElements('populations').val();
                            console.log('Options');
                            console.log(console);
                            return (options != null && options.length >= 1);
                        }
                    }
                }
            }
        }
    });

}
