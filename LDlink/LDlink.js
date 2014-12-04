var restService = {
  protocol : 'http',
  hostname : document.location.hostname,
  fqn : "nci.nih.gov",
  port : 9090,
  route : "LDlinkRest"
}

var restServerUrl = restService.protocol + "://" + restService.hostname + "/"
    + restService.route;

var populations = {
	AFR : {
		fullName : "African",
		subPopulations : {
			YRI : "Yoruba in Ibadan, Nigera",
			LWK : "	Luhya in Webuye, Kenya",
			GWD : "	Gambian in Western Gambia",
			MSL : "	Mende in Sierra Leone",
			ESN : "	Esan in Nigera",
			ASW : "	Americans of African Ancestry in SW USA",
			ACB : "	African Carribbeans in Barbados"
		}
	},
	AMR : {
		fullName : "Ad Mixed American",
		subPopulations : {
			MXL : "	Mexican Ancestry from Los Angeles, USA",
			PUR : "	Puerto Ricans from Puerto Rico",
			CLM : "	Colombians from Medellin, Colombia",
			PEL : "	Peruvians from Lima, Peru"
		}
	},
	EAS : {
		fullName : "East Asian",
		subPopulations : {
			CHB : "	Han Chinese in Bejing, China",
			JPT : "	Japanese in Tokyo, Japan",
			CHS : "	Southern Han Chinese",
			CDX : "	Chinese Dai in Xishuangbanna, China",
			KHV : "	Kinh in Ho Chi Minh City, Vietnam"
		}
	},
	EUR : {
		fullName : "European",
		subPopulations : {
			CEU : "	Utah Residents from North and West Europe",
			TSI : "	Toscani in Italia",
			FIN : "	Finnish in Finland",
			GBR : "	British in England and Scotland",
			IBS : "	Iberian population in Spain"
		}
	},
	SAS : {
		fullName : "South Asian",
		subPopulations : {
			GIH : "	Gujarati Indian from Houston, Texas",
			PJL : "	Punjabi from Lahore, Pakistan",
			BEB : "	Bengali from Bangladesh",
			STU : "	Sri Lankan Tamil from the UK",
			ITU : "	Indian Telugu from the UK"
		}
	}
}


function buildPopulationDropdown(elementId) {
	var htmlText = "";
	var htmlText1 = "<optgroup value='ABBREV' label='(ABBREV) FULLNAME'>\n";
	var htmlText2 = "<option value='ABBREV'>(ABBREV) DETAIL </option>\n";
	for ( var popAbbrev in populations) {
		var population = populations[popAbbrev];
		htmlText += htmlText1.replace(/ABBREV/g, popAbbrev).replace("FULLNAME",
				population.fullName);
		for ( var subPopAbbrev in population.subPopulations) {
			var subDetail = population.subPopulations[subPopAbbrev];
			htmlText += htmlText2.replace(/ABBREV/g, subPopAbbrev).replace(
					"DETAIL", subDetail);
		}
		htmlText += "</optgroup>\n";
	}
	$('#' + elementId).html(htmlText);

	$('#' + elementId)
			.multiselect(
					{
						enableClickableOptGroups : true,
						buttonWidth : '300px',
						maxHeight : 500,
						includeSelectAllOption : true,
						dropRight : true,
						allSelectedText : 'All Populations',
						nonSelectedText : 'Select Population',
						numberDisplayed : 6,
						selectAllText : ' (ALL) All Populations',

						// buttonClass: 'btn btn-link',
						buttonText : function(options, select) {
							if (options.length === 0) {
								return this.nonSelectedText
										+ ' <b class="caret"></b>';
							} else if (options.length == $('option', $(select)).length) {
								return this.allSelectedText
										+ ' <b class="caret"></b>';
							} else if (options.length > this.numberDisplayed) {
								return '<span class="badge">' + options.length
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


var ldPairData =[
{
  "corr_alleles": [
    "rs2720460(A) allele is correlated with rs11733615(C) allele",
    "rs2720460(G) allele is correlated with rs11733615(T) allele"
  ],
  "haplotypes": {
    "hap1": {
      "alleles": "AC",
      "count": "155",
      "frequency": "0.686"
    },
    "hap2": {
      "alleles": "GC",
      "count": "40",
      "frequency": "0.177"
    },
    "hap3": {
      "alleles": "GT",
      "count": "29",
      "frequency": "0.128"
    },
    "hap4": {
      "alleles": "AT",
      "count": "2",
      "frequency": "0.009"
    }
  },
  "snp1": {
    "allele_1": {
      "allele": "A",
      "count": "157",
      "frequency": "0.695"
    },
    "allele_2": {
      "allele": "G",
      "count": "69",
      "frequency": "0.305"
    },
    "coord": "chr4:104054686",
    "rsnum": "rs2720460"
  },
  "snp2": {
    "allele_1": {
      "allele": "C",
      "count": "195",
      "frequency": "0.863"
    },
    "allele_2": {
      "allele": "T",
      "count": "31",
      "frequency": "0.137"
    },
    "coord": "chr4:104157164",
    "rsnum": "rs11733615"
  },
  "statistics": {
    "chisq": "67.271",
    "d_prime": "0.9071",
    "p": "0.0",
    "r2": "0.2977"
  },
  "two_by_two": {
    "cells": {
      "c11": "155",
      "c12": "2",
      "c21": "40",
      "c22": "29"
    },
    "total": "old - 227"
  }
}];


var ldProxyData ={
  top10:  [{"Alleles":"newProxy","Coord":"chr12:126891966","Corr_Alleles":"G-G,A-A","Dist":986,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs7957025","RegulomeDB":"5"},{"Alleles":"(A/G)","Coord":"chr12:126888368","Corr_Alleles":"G-A,A-G","Dist":-2612,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs10847146","RegulomeDB":"5"},{"Alleles":"(T/A)","Coord":"chr12:126894660","Corr_Alleles":"G-T,A-A","Dist":3680,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs11058634","RegulomeDB":"7"},{"Alleles":"(G/C)","Coord":"chr12:126887133","Corr_Alleles":"G-G,A-C","Dist":-3847,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs11058630","RegulomeDB":"6"},{"Alleles":"(G/A)","Coord":"chr12:126895215","Corr_Alleles":"G-G,A-A","Dist":4235,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs11058636","RegulomeDB":"7"},{"Alleles":"(G/T)","Coord":"chr12:126895996","Corr_Alleles":"G-G,A-T","Dist":5016,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs7972985","RegulomeDB":"6"},{"Alleles":"(C/T)","Coord":"chr12:126885179","Corr_Alleles":"G-C,A-T","Dist":-5801,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs61942997","RegulomeDB":"5"},{"Alleles":"(A/G)","Coord":"chr12:126884784","Corr_Alleles":"G-A,A-G","Dist":-6196,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs12579545","RegulomeDB":"7"},{"Alleles":"(G/A)","Coord":"chr12:126898373","Corr_Alleles":"G-G,A-A","Dist":7393,"Dprime":"1.0","Function":"unknown","MAF":"0.138888888889","R2":1,"RS":"rs7132131","RegulomeDB":"7"}]
};

//Map knockout models to a sample json data
var ldproxyModel = ko.mapping.fromJS(ldProxyData);
var ldpairModel = ko.mapping.fromJS(ldPairData[0]);

//Set file support trigger
$(document)
		.on(
				'change',
				'.btn-file :file',
				function() {
					var input = $(this), numFiles = input.get(0).files ? input
							.get(0).files.length : 1, label = input.val()
							.replace(/\\/g, '/').replace(/.*\//, '');
					input.trigger('fileselect', [ numFiles, label ]);
				});


$(document).ready(function() {

      var modules = ["ldhap", "ldmatrix", "ldpair", "ldproxy"];

			// Apply Bindings
			ko.applyBindings(ldpairModel, document.getElementById('ldpair-results-container'));
      ko.applyBindings(ldproxyModel, document.getElementById('ldproxy-results-container'));
      console.log('ldpairModel');
      console.dir(ldpairModel);
      console.log('ldproxyModel');
      console.dir(ldproxyModel);

			$.each(modules, function(key, id) {
				buildPopulationDropdown(id+"-population-codes");
        $("#"+id+"-results-container").hide();
        $('#'+id+'-message').hide();
        $('#'+id+'-message-warning').hide();
			});

			$('.tab-content').on('click',
					"a[class|='btn btn-default calculate']", function(e) {
						calculate(e);
			});
      $('.tab-content').on('click',
        "button[class|='btn btn-default calculate']", function(e) {
            calculate(e);
      });

  // Add file select listeners

	$('.btn-file :file')
		.on(
			'fileselect',
			function(event, numFiles, label) {
        populateTextArea(event, numFiles, label);
				console.log("numFiles: " + numFiles);
				console.log("label: " + label);
				var input = $(this).parents('.input-group').find(':text'),
              log = numFiles > 1 ? numFiles + ' files selected' : label;
							if (input.length) {
								input.val(log);
						  } else {
								if (log)
									alert(log);
			        }
		});

//
// HERE IS HOW IT IS DONE
//  https://developer.mozilla.org/en-US/docs/Web/Guide/Using_FormData_Objects
//
});

function populateTextArea(event, numFiles, label) {
  id = event.target.id;
  if(window.FileReader) {

    var input = event.target;
    var reader = new FileReader();
    reader.onload = function(){
      var text = reader.result;
      $('#'+id+'-snp-numbers').val(text);
      console.log("Append to textarea");
      console.log(reader.result.substring(0, 10000));
    };
    reader.readAsText(input.files[0]);
  } else {
    alert('FileReader not supported');
    return;
  }
}

function calculate(e) {
	var id = e.target.id;
  e.preventDefault();
//	var firstClick = $('#'+id+'-results-container').hasClass( "hidden" );

  $('#'+id+'-results-container').hide();
  $('#'+id+'-message').hide();
  $('#'+id+'-message-warning').hide();

 	updateData(id);
}

function updateData(id) {
	//Make this generic...
	//ie. prepare url and post data.
	//Get data...
	var data;
	switch (id) {
	case 'ldpair':
					updateLDpair();
		break;
	case 'ldproxy':
      $('#'+id+'-progress-container').show();
      //ko.mapping.fromJS(newProxy4, ldproxyModel);
      updateLDproxy();
      updateProgressBar(id, 30);
		break;
	case 'ldmatrix':
      console.log($('#ldmatrix-form').serialize());
      updateLDmatrix();
		break;
	case 'ldhap':
		break;
	}

}

function updateLDmatrix() {
  var id = "ldmatrix";

  var $btn = $('#'+id).button('loading');
//    snp : $('#ldmatrix-snp').val(),
  var snps = $('#'+id+'-file-snp-numbers').val();
  var population = $('#'+id+'-population-codes').val();
  //var snps = snps.replace("\n", ",");
  //alert(snps);
  //alert(population);
  console.log("snps");
  console.dir(snps);
  console.log("population");
  console.dir(population);

  var ldmatrixInputs = {
    snps: snps,
    pop : population.join("+"),
    reference : Math.floor(Math.random() * (99999 - 10000 + 1))
  };
  console.log('ldmatrixInputs');
  console.dir(ldmatrixInputs);
/*
  var ajaxType;
  // The Javascript
  var fileInput = document.getElementById('ldmatrix-file');
  var formData = new FormData();

  if($("#ldmatrix-file").val() == '') {
    ajaxType = 'GET';
  } else {
    //Append file to post
    ajaxType = 'POST';
    var file = fileInput.files[0];
    formData.append('file', file);
    formData.append('filename', file.name);
    formData.append('filetype', file.type);
  }
  formData.append('pop', ldmatrixInputs.pop);


  console.log("formData");
  console.dir(formData);
*/


  var url = restServerUrl + "/ldmatrix";
  var ajaxRequest = $.ajax({
    type : 'GET',
    url : url,
    data : ldmatrixInputs
  });

  ajaxRequest.success(function(data) {
      // SUCCESS
      console.log("SUCCESS");
      $('#ldmatrix-bokeh-graph').empty().append(data);
      $('#'+id+'-progress-container').hide();
      $('#'+id+'-results-container').show();

      addLDMatrixHyperLinks(ldmatrixInputs.reference);

      //getLDProxyResults('proxy'+ldproxyInputs.reference+'.json');
/*
    setTimeout(function(){
      var proxyTop = getProxyTop10();
      ko.mapping.fromJS(proxyTop, ldproxyModel);
      //alert("Hello");
    }, 9000);
*/
      //Get the top 10...
      //createProxyTop10();

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
function updateProgressBar(id, seconds) {
  var milliseconds = seconds * 1000;
  // Divide number of milliseconds to get 100 to get 100 updates
  var delay = milliseconds / 100;

//  $('#'+id+'-progress').show();

    //var progressBar = $('#'+id+' div:first-child');
    var progressBar = $('.progress-bar');
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


function addPageListeners(tabClicked) {
	if (tabClicked == 'ldhap') {
		$('.btn-file :file')
				.on(
						'fileselect',
						function(event, numFiles, label) {
							console.log("numFiles: " + numFiles);
							console.log("label: " + label);

							var input = $(this).parents('.input-group').find(
									':text'), log = numFiles > 1 ? numFiles
									+ ' files selected' : label;

							if (input.length) {
								input.val(log);
							} else {
								if (log)
									alert(log);
							}
		});
	}
}

function createPopulationDropdown(id) {

  $('#' + id + '-population-codes')
			.multiselect(
					{
						enableClickableOptGroups : true,
						buttonWidth : '300px',
						maxHeight : 500,
						includeSelectAllOption : true,
						dropRight : true,
						allSelectedText : 'All Populations',
						nonSelectedText : 'Select Population',
						numberDisplayed : 6,
						selectAllText : ' (ALL) All Populations',

						// buttonClass: 'btn btn-link',
						buttonText : function(options, select) {
							if (options.length === 0) {
								return this.nonSelectedText
										+ ' <b class="caret"></b>';
							} else if (options.length == $('option', $(select)).length) {
								return this.allSelectedText
										+ ' <b class="caret"></b>';
							} else if (options.length > this.numberDisplayed) {
								return '<span class="badge">' + options.length
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

  $('#ldproxy-results-link').attr('href', 'tmp/proxy'+ldproxyInputs.reference+'.txt');

  var url = restServerUrl + "/ldproxy";
  var ajaxRequest = $.ajax({
    type : "GET",
    url : url,
    data : ldproxyInputs
  });

  ajaxRequest.success(function(data) {
      // SUCCESS
      console.log("SUCCESS");
      $('#ldproxy-bokeh-graph').empty().append(data);
      $('#'+id+'-progress-container').hide();
      $('#'+id+'-results-container').show();
      getLDProxyResults('proxy'+ldproxyInputs.reference+'.json');
/*
    setTimeout(function(){
      var proxyTop = getProxyTop10();
      ko.mapping.fromJS(proxyTop, ldproxyModel);
      //alert("Hello");
    }, 9000);
*/
      //Get the top 10...
      //createProxyTop10();

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
  });
  ajaxRequest.fail(function(jqXHR, textStatus) {
    alert('Fail');
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
	var population = $('#ldpair-population-codes').val();
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
    var id = 'ldpair';
    if(data.warning) {
      $('#'+id+'-message-warning').show();
      $('#'+id+'-message-warning-content').empty().append(data.warning);
    }

		if (data.error) {
      // ERROR
      $('#'+id+'-message').show();
      $('#'+id+'-message-content').empty().append(data.error);
		} else {
      // SUCCESS
      ko.mapping.fromJS(data, ldpairModel);
      $('#'+id+'-results-container').show();
      addHyperLinks(data);
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
		console.log("second complete");

	});
}

function addHyperLinks(data) {
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


/*
jQuery.fn.serializeObject = function() {
	var o = {};
	var a = this.serializeArray();
	jQuery.each(a, function() {
		if (o[this.id] !== undefined) {
			if (!o[this.id].push) {
				o[this.id] = [ o[this.id] ];
			}
			o[this.id].push(this.value || '');
		} else {
			o[this.id] = this.value || '';
		}
	});
	return o;
};
*/
