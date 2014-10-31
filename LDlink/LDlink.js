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

$( document ).ready(function() {

	console.log( "ready!" );
    /*
    $('.calculate').on.('click', function(e){
        console.log('You clicked calculate');

    });
*/
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
                console.log(val.substring(1, val.length)+'-population-codes');
                createPopulationDropdown(val.substring(1, val.length)+'-population-codes');
                appendJumboTron(val.substring(1, val.length));
                $('.active a').attr('loaded','true');
            });
        }
    });

// load first tab content
//$("#home").append("<h1>Hello</h1>");
//$('.active a').tab('show');
    $('#home').load($('.active a').attr("data-url"), function(result){
        $('.active a').attr('loaded','true');
        $('.active a').tab('show');
    });

/*
    $('#home').load($('.active a').attr("data-url"), function(result){
        $('.active a').tab('show');
    });
*/

});

function calculate(e) {
    var id = e.target.id;
    console.log('CALCULATE '+id);
    //Put a switch here for all the different types of caclulate buttons.
    if(id == 'ldpair-calculate-button') {
        //alert('got it');
        $('#ldpair-results-container').load('ldpair.results.template.html', function(){
            bindLDpair();
            //TODO:  Disable button for demo purpose only.
            $('#ldpair-calculate-button').prop("disabled",true);;

        });
        //ko.applyBindings(new PatientViewModel(), document.getElementById('match-patient'));
        // Activates knockout.js
        //ko.applyBindings(new AppViewModel(), document.getElementById('names'));      
        // Activates knockout.js
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

    $('#'+id).multiselect({
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
                    selected += $(this).val() + ', ';
                });
                
                return selected.substr(0, selected.length - 2) + ' <b class="caret"></b>';
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
    ko.applyBindings(new AppViewModel());  
}

// This is a simple *viewmodel* - JavaScript that defines the data and behavior of your UI
function AppViewModel() {
    this.firstName = ko.observable("Bert");
    this.lastName = ko.observable("Bertington");
    this.ldpair = ldpair[0];
    console.log('AppViewModel');
    console.dir(this);
}
