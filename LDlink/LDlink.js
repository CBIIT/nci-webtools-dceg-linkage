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

var restService = {
	protocol : 'http',
	hostname : document.location.hostname,
	fqn : "nci.nih.gov",
	port : 9090,
	route : "LDlinkRest"
}

var restServerUrl = restService.protocol + "://" + restService.hostname + "/"
		+ restService.route;

var ldpairNewData =[
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

var ldpairModel = ko.mapping.fromJS(ldpairNewData[0]);

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

var modules = ["ldhap", "ldmatrix", "ldpair", "ldproxy"];


$(document).ready(
		function() {
			// Apply Bindings
			ko.applyBindings(ldpairModel, document.getElementById('ldpair-results-container'));

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

  // Add file select listeners

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

});

function calculate(e) {
	var id = e.target.id;
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
      //alert("You clicked ldproxy.  What to do now");
      $('#'+id+'-results-container').show();

      var url = 'http://analysistools-sandbox.nci.nih.gov/LDlinkRest/ldproxy?snp=rs2720460&pop=EUR&reference=proxy3';
      $('#'+id+'-results-container').load(url, function() {
        console.log('ldproxy_json');
        console.dir(ldproxy_json);
      });

		break;
	case 'ldheat':
		break;
	case 'ldhap':
		break;
	}

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
	// var url = "http://"+location.hostname+":8090/LDlinkRest/ldpair";
	// var url = "http://"+location.hostname+"/LDlinkRest/ldpair";
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
				+ "\n\nMake sure Plask Python server is available.");
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

/*
1.  Add dbSNP link to snp1.rsnum and snp2.rsnum

e.g. for SNP rs2720460, add the following link
http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=2720460

2.  Add UCSC Genome Browser link to snp1.coord and snp2.coord

e.g. for SNP rs2720460, chromosome position chr4:104054686, add the following link

http://genome.ucsc.edu/cgi-bin/hgTracks?position=chr4:104054436-104054936&snp141=pack&hgFind.matches=rs2720460

Use plus and minus 250 bp from the given coordinates.

3.  Bring up these two links as two separate browser tabs.
*/
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
