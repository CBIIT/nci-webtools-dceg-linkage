var restService = {
  protocol: 'http',
  hostname: document.location.hostname,
  fqn: "nci.nih.gov",
  port:9090,
  route: "LDlinkRest"
}

var restServerUrl = restService.protocol
                      +"://"+restService.hostname
                      +"/"+restService.route; 


var ldpair =[
{
 "corr_alleles": [
  "rs2720460(A) allele is correlated with rs11733615(C) allele",
  "rs2720460(G) allele is correlated with rs11733615(T) allele"
 ],
 "haplotypes": {
  "hap1": {
   "alleles": "AC",
   "count": "576",
   "frequency": "0.573"
  },
  "hap2": {
   "alleles": "GT",
   "count": "361",
   "frequency": "0.359"
  },
  "hap3": {
   "alleles": "GC",
   "count": "42",
   "frequency": "0.042"
  },
  "hap4": {
   "alleles": "AT",
   "count": "27",
   "frequency": "0.027"
  }
 },
 "snp1": {
  "allele_1": {
   "allele": "A",
   "count": "603",
   "frequency": "0.599"
  },
  "allele_2": {
   "allele": "G",
   "count": "403",
   "frequency": "0.401"
  },
  "coord": "chr4:104054686",
  "rsnum": "rs2720460"
 },
 "snp2": {
  "allele_1": {
   "allele": "C",
   "count": "618",
   "frequency": "0.614"
  },
  "allele_2": {
   "allele": "T",
   "count": "388",
   "frequency": "0.386"
  },
  "coord": "chr4:104157164",
  "rsnum": "rs11733615"
 },
 "statistics": {
  "chisq": "738.354",
  "d_prime": "0.8839",
  "p": "0.0",
  "r2": "0.734"
 },
 "two_by_two": {
  "cells": {
   "c11": "576",
   "c12": "27",
   "c21": "42",
   "c22": "361"
  },
  "total": "1006"
 }
}
];

$(document).on('change', '.btn-file :file', function() {
  var input = $(this),
  numFiles = input.get(0).files ? input.get(0).files.length : 1,
  label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
  input.trigger('fileselect', [numFiles, label]);
});

$( document ).ready(function() {

	console.log( "ready!" );
  console.log("restServerUrl");
  console.log(restServerUrl);
    $('.tab-content').on('click',"a[class|='btn btn-primary calculate']", function(e){
        calculate(e);
    });
    $('#ldlink-tabs a').click(function (e) {
        e.preventDefault();
        //alert($(this).attr("data-url"));
        var url = $(this).attr("data-url");
        var href = this.hash;
        var pane = $(this);
        var loaded = $(this).attr("loaded");
        console.log('url: '+url);
        console.log('href: '+href);
        console.log('pane: '+pane);
        console.log('loaded: '+loaded);
        console.log('About to load');

        if(loaded == "false") {
            // ajax load from data-url
            $(href).load(url,function(result){      
                pane.tab('show');
                console.log('HREF: '+href);
                var val = href;
                console.log('Creating: '+val.substring(1, val.length));
                createPopulationDropdown(val.substring(1, val.length));
                appendJumboTron(val.substring(1, val.length));
                addPageListeners(val.substring(1, val.length));
                $('.active a').attr('loaded','true');
            });
        }
    });

    $('#home').load($('.active a').attr("data-url"), function(result){
        $('.active a').attr('loaded','true');
        $('.active a').tab('show');
    });
});

function addPageListeners(tabClicked) {
  if(tabClicked == 'ldhap') {
    $('.btn-file :file').on('fileselect', function(event, numFiles, label) {
      console.log("numFiles: " + numFiles);
      console.log("label: " + label);

      var input = $(this).parents('.input-group').find(':text'),
          log = numFiles > 1 ? numFiles + ' files selected' : label;

      if( input.length ) {
          input.val(log);
      } else {
          if( log ) alert(log);
      }
    });
  }

}

function calculate(e) {
  var id = e.target.id;
  console.log('CALCULATE: '+id);
  switch(id) {
      case 'ldpair-calculate-button':
        $('#ldpair-results-container').load('ldpair.results.template.html', function(){
            bindLDpair();
            //TODO:  Disable button for demo purpose only.
            $('#ldpair-calculate-button').prop("disabled",true);;
        });
        break;
      case 'ldproxy-calculate-button':
        $('#ldproxy-results-container').load('ldproxy.results.template.html', function(){
            //TODO:  Disable button for demo purpose only.
            $('#ldproxy-calculate-button').prop("disabled",true);;
        });
          break;
      case 'ldheat-calculate-button':
        $('#ldheat-results-container').load('ldheat.results.template.html', function(){
            //TODO:  Disable button for demo purpose only.
            $('#ldheat-calculate-button').prop("disabled",true);;
        });
          break;
      case 'ldhap-calculate-button':
        $('#ldhap-results-container').load('ldhap.results.template.html', function(){
            //TODO:  Disable button for demo purpose only.
            $('#ldhap-calculate-button').prop("disabled",true);;
        });
          break;
  }

}

function appendJumboTron(id) {

    $("#"+id).append(
        $('<div/>', {'class': 'jumbotron'}).append(
            $('<div/>', {'class': 'container'})
                .append("    Results ...<br><br><br><br><br><br><br><br><br><br><br><br><br><br>")
                .attr('id', id+'-results-container')
        )
    );

}

function createPopulationDropdown(id) {

    $('#'+id+'-population-codes').multiselect({
        enableClickableOptGroups: true, 
        buttonWidth: '300px',
        maxHeight: 500,
        includeSelectAllOption: true,
        dropRight: true,
        allSelectedText: 'All Populations',
        nonSelectedText: 'Select Population',
        numberDisplayed: 6,
        selectAllText: ' (ALL) All Populations',

        //buttonClass: 'btn btn-link',
        buttonText: function(options, select) {
            if (options.length === 0) {
                return this.nonSelectedText + ' <b class="caret"></b>';
            }
            else if (options.length == $('option', $(select)).length) {
                return this.allSelectedText + ' <b class="caret"></b>';
            }
            else if (options.length > this.numberDisplayed) {
                return '<span class="badge">'+options.length+'</span> ' + this.nSelectedText + ' <b class="caret"></b>';
            }
            else {
                var selected = '';
                options.each(function() {
                    //var label =  $(this).attr('label') : $(this).html();
                    selected += $(this).val() + '+';
                });
                
                return selected.substr(0, selected.length - 1) + ' <b class="caret"></b>';
            }
        },
        buttonTitle: function(options, select) {
            if (options.length === 0) {
                return this.nonSelectedText;
            } else {
                var selected = '';
                options.each(function () {
                    selected += $(this).text() + '\n';
                });
                return selected;
            }
        }
    });
}

function PatientViewModel() {
    this._id = patient[0]._id;
    this.patientSequenceNumber = ko.observable(patient[0].patientSequenceNumber);
    this.registrationDate = patient[0].registrationDate;
    this.firstName = ko.observable("Bert");
    this.lastName = ko.observable("Bertington");
    this.fullName = ko.computed(function() {
        return this.firstName() + " " + this.lastName();    
    }, this);
}

function bindLDpair() {
    var ldpairInputs = {
        snp1: $('#ldpair-snp1').val(),
        snp2: $('#ldpair-snp2').val(),
        populations: $('#ldpair-population-codes').val(),
        reference: Math.floor(Math.random() * (99999 - 10000 + 1)) + 10000 
    };
    /*
    var myDropDownListValues = $("#ldpair-population-codes").multiselect("getSelected").map(function()
        {
            return this.value;    
        }).get();
*/
    //console.log(myDropDownListValues);
    //alert($('#ldpair-population-codes').multiselect('getSelected'));
    //alert($('#ldpair-population-codes').val());
    //alert("about to get inputs");
    //var ldpairInputs = $('#ldpair-inputs-form').serializeObject();
    console.log("ldpairInputs");
    //alert(ldpairInputs);
    //alert(JSON.stringify(ldpairInputs));
    //console.log(JSON.stringify(ldpairInputs));
    console.dir(ldpairInputs);
    //alert(yourObject);
    //var url = "http://"+location.hostname+":8090/LDlinkRest/ldpair";
    //var url = "http://"+location.hostname+"/LDlinkRest/ldpair";
    var url = restServerUrl+"/ldpair";
  //var url = "http://analysistools-sandbox.nci.nih.gov/LDlinkRest/ldpair";
    //alert(url);

    /*  
    $.getJSON(url, function(data) { 
    // Now use this data to update your view models, 
    // and Knockout will update your UI automatically 
        console.log("DATA");
        console.dir(data);
      //  alert(data);

    }); 
    */

// Assign handlers immediately after making the request,
// and remember the jqXHR object for this request

    var jqxhr = $.ajax({
        type: "GET",
        url: url,
        data: ldpairInputs,        
    }).done(function() {
        console.log("done");
    }).fail(function() {
        console.log("error");
    }).always(function() {
        console.log("complete");
    });
// Perform other work here ...
// Set another completion function for the request above
    jqxhr.always(function() {
        //Load file
        $console.log("second complete");
        alert("complete load file");
        

    });    

//    $('#ldpair-results-data').load(url);
    ko.applyBindings(new LDpairViewModel()); 
}

// This is a simple *viewmodel* - JavaScript that defines the data and behavior of your UI
function LDpairViewModel() {
    //this.parameter.snp1 = ko.observable("Bert");
    //this.parameter.snp2 = ko.observable("Bertington");
    //this.parameter.populations = ko.observableArray(["Cat", "Dog", "Fish"])
    this.ldpair = ldpair[0];
    console.log('LDpairViewModel');
    console.dir(this);
}


jQuery.fn.serializeObject = function() {
    var o = {};
    var a = this.serializeArray();
    jQuery.each(a, function() {
        if (o[this.id] !== undefined) {
            if (!o[this.id].push) {
                o[this.id] = [o[this.id]];
            }
            o[this.id].push(this.value || '');
        } else {
            o[this.id] = this.value || '';
        }
    });
    return o;
};

/* Ajax calls*/
