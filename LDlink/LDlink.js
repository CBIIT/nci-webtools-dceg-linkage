var ldlink_version = "Version 2.0";

var restService = {
	protocol : 'http',
	hostname : document.location.hostname,
	fqn : "nci.nih.gov",
	port : 9090,
	route : "LDlinkRest"
}

var restServerUrl = restService.protocol + "://" + restService.hostname + "/"+ restService.route;
var populations={AFR:{fullName:"African",subPopulations:{YRI:"Yoruba in Ibadan, Nigera",LWK:" Luhya in Webuye, Kenya",GWD:" Gambian in Western Gambia",MSL:"  Mende in Sierra Leone",ESN:"  Esan in Nigera",ASW:" Americans of African Ancestry in SW USA",ACB:"  African Carribbeans in Barbados"}},AMR:{fullName:"Ad Mixed American",subPopulations:{MXL:"  Mexican Ancestry from Los Angeles, USA",PUR:" Puerto Ricans from Puerto Rico",CLM:" Colombians from Medellin, Colombia",PEL:" Peruvians from Lima, Peru"}},EAS:{fullName:"East Asian",subPopulations:{CHB:" Han Chinese in Bejing, China",JPT:" Japanese in Tokyo, Japan",CHS:" Southern Han Chinese",CDX:" Chinese Dai in Xishuangbanna, China",KHV:"  Kinh in Ho Chi Minh City, Vietnam"}},EUR:{fullName:"European",subPopulations:{CEU:" Utah Residents from North and West Europe",TSI:"  Toscani in Italia",FIN:"  Finnish in Finland",GBR:" British in England and Scotland",IBS:"  Iberian population in Spain"}},SAS:{fullName:"South Asian",subPopulations:{GIH:"  Gujarati Indian from Houston, Texas",PJL:"  Punjabi from Lahore, Pakistan",BEB:"  Bengali from Bangladesh",STU:"  Sri Lankan Tamil from the UK",ITU:" Indian Telugu from the UK"}}};
var ldPairData={corr_alleles:["rs2720460(A) allele is correlated with rs11733615(C) allele","rs2720460(G) allele is correlated with rs11733615(T) allele"],haplotypes:{hap1:{alleles:"AC",count:"155",frequency:"0.686"},hap2:{alleles:"GC",count:"40",frequency:"0.177"},hap3:{alleles:"GT",count:"29",frequency:"0.128"},hap4:{alleles:"AT",count:"2",frequency:"0.009"}},snp1:{allele_1:{allele:"A",count:"157",frequency:"0.695"},allele_2:{allele:"G",count:"69",frequency:"0.305"},coord:"chr4:104054686",rsnum:"rs2720460"},snp2:{allele_1:{allele:"C",count:"195",frequency:"0.863"},allele_2:{allele:"T",count:"31",frequency:"0.137"},coord:"chr4:104157164",rsnum:"rs11733615"},statistics:{chisq:"67.271",d_prime:"0.9071",p:"0.0",r2:"0.2977"},two_by_two:{cells:{c11:"155",c12:"2",c21:"40",c22:"29"},total:"old - 227"}};
var ldhapData={footer:[{Count:127,Frequency:.588,Haplotype:"GCATGGCGTTGGGG"},{Count:40,Frequency:.1852,Haplotype:"GGGGAGCGTTGGGG"},{Count:23,Frequency:.1065,Haplotype:"GCGGAGCGTTGGGG"},{Count:11,Frequency:.0509,Haplotype:"TGGGAGCGTTGGGG"},{Count:8,Frequency:.037,Haplotype:"GCATAGCGTTGGGG"},{Count:7,Frequency:.0324,Haplotype:"TGGGGATAGCAAAG"}],rows:[{Alleles:"G=0.917, T=0.083",Coord:"chr4:104050980",RS:"rs2720457",Haplotypes:["G","G","G","T","G","T"]},{Alleles:"C=0.732, G=0.269",Coord:"chr4:104052963",RS:"rs2720458",Haplotypes:["C","G","C","G","C","G"]},{Alleles:"A=0.625, G=0.375",Coord:"chr4:104055748",RS:"rs2720461",Haplotypes:["A","G","G","G","A","G"]},{Alleles:"T=0.625, G=0.375",Coord:"chr4:104056210",RS:"rs2720462",Haplotypes:["T","G","G","G","T","G"]},{Alleles:"G=0.62, A=0.38",Coord:"chr4:104052068",RS:"rs7661201",Haplotypes:["G","A","A","A","A","G"]},{Alleles:"G=0.968, A=0.032",Coord:"chr4:104055722",RS:"rs2623063",Haplotypes:["G","G","G","G","G","A"]},{Alleles:"C=0.968, T=0.032",Coord:"chr4:104057121",RS:"rs2623062",Haplotypes:["C","C","C","C","C","T"]},{Alleles:"G=0.968, A=0.032",Coord:"chr4:104057248",RS:"rs2720463",Haplotypes:["G","G","G","G","G","A"]},{Alleles:"T=0.968, G=0.032",Coord:"chr4:104057887",RS:"rs2711901",Haplotypes:["T","T","T","T","T","G"]},{Alleles:"T=0.968, C=0.032",Coord:"chr4:104051132",RS:"rs2623082",Haplotypes:["T","T","T","T","T","C"]},{Alleles:"G=0.968, A=0.032",Coord:"chr4:104058596",RS:"rs2711900",Haplotypes:["G","G","G","G","G","A"]},{Alleles:"G=0.968, A=0.032",Coord:"chr4:104050510",RS:"rs2720456",Haplotypes:["G","G","G","G","G","A"]},{Alleles:"G=0.968, A=0.032",Coord:"chr4:104050326",RS:"rs2720455",Haplotypes:["G","G","G","G","G","A"]},{Alleles:"G=1.0, A=0.0",Coord:"chr4:104059542",RS:"rs2243682",Haplotypes:["G","G","G","G","G","G"]}]};
//var ldClipData1={details:{rs1:["NA","NA","SNP not found in dbSNP142, SNP removed."],rs111531283:["chr19:39738317","A=0.737, C=0.263","SNP in LD with rs11322783 (R2=0.2849), SNP removed"],rs11322783:["chr19:39739153","T=0.444, -=0.556","SNP kept"],rs11881222:["chr19:39734923","A=0.672, G=0.328","SNP in LD with rs11322783 (R2=0.2245), SNP removed"],rs11882871:["chr19:39737610","A=0.475, G=0.525","SNP in LD with rs11322783 (R2=0.6373), SNP removed"],rs12979860:["chr19:39738787","C=0.485, T=0.515","SNP in LD with rs11322783 (R2=0.85), SNP removed"],rs12980275:["chr19:39731783","A=0.556, G=0.444","SNP in LD with rs11322783 (R2=0.3546), SNP removed"],rs12980602:["chr19:39752820","T=0.763, C=0.237","SNP kept"],rs2:["NA","NA","SNP not found in dbSNP142, SNP removed."],rs35963157:["chr19:39745695","-=0.338, C=0.662","SNP in LD with rs11322783 (R2=0.1887), SNP removed"],rs368234815:["NA","NA","Variant not in 1000G VCF file, variant removed"],rs4803217:["chr19:39734220","C=0.47, A=0.53","SNP in LD with rs11322783 (R2=0.6526), SNP removed"],rs4803222:["chr19:39739353","G=0.747, C=0.253","SNP in LD with rs11322783 (R2=0.2703), SNP removed"],rs6508852:["chr19:39752262","A=0.263, G=0.737","SNP in LD with rs8101517 (R2=0.609), SNP removed"],rs66477315:["chr19:39751674","T=0.636, -=0.364","SNP in LD with rs8101517 (R2=0.1736), SNP removed"],rs688187:["chr19:39732752","G=0.465, A=0.535","SNP in LD with rs11322783 (R2=0.6682), SNP removed"],rs7248668:["chr19:39743821","G=0.924, A=0.076","SNP in LD with rs8099917 (R2=1.0), SNP removed"],rs74597329:["chr19:39739155","T=0.444, G=0.556","SNP in LD with rs11322783 (R2=1.0), SNP removed"],rs78605718:["chr19:39745812","C=0.904, T=0.096","SNP kept"],rs8099917:["chr19:39743165","T=0.924, G=0.076","SNP kept"],rs8101517:["chr19:39747741","A=0.328, C=0.672","SNP kept"],rs8103142:["chr19:39735106","T=0.424, C=0.576","SNP in LD with rs11322783 (R2=0.6), SNP removed"],rs8109886:["chr19:39742762","C=0.253, A=0.747","SNP in LD with rs11322783 (R2=0.4223), SNP removed"],rs955155:["chr19:39729479","G=0.96, A=0.04","SNP kept"]},snp_list:["rs11322783","rs8099917","rs955155","rs8101517","rs12980602","rs78605718"]};
var ldClipDetails={rs1:["NA","NA","SNP not found in dbSNP142, SNP removed."],rs111531283:["chr19:39738317","A=0.737, C=0.263","SNP in LD with rs11322783 (R2=0.2849), SNP removed"],rs11322783:["chr19:39739153","T=0.444, -=0.556","SNP kept"],rs11881222:["chr19:39734923","A=0.672, G=0.328","SNP in LD with rs11322783 (R2=0.2245), SNP removed"],rs11882871:["chr19:39737610","A=0.475, G=0.525","SNP in LD with rs11322783 (R2=0.6373), SNP removed"],rs12979860:["chr19:39738787","C=0.485, T=0.515","SNP in LD with rs11322783 (R2=0.85), SNP removed"],rs12980275:["chr19:39731783","A=0.556, G=0.444","SNP in LD with rs11322783 (R2=0.3546), SNP removed"],rs12980602:["chr19:39752820","T=0.763, C=0.237","SNP kept"],rs2:["NA","NA","SNP not found in dbSNP142, SNP removed."],rs35963157:["chr19:39745695","-=0.338, C=0.662","SNP in LD with rs11322783 (R2=0.1887), SNP removed"],rs368234815:["NA","NA","Variant not in 1000G VCF file, variant removed"],rs4803217:["chr19:39734220","C=0.47, A=0.53","SNP in LD with rs11322783 (R2=0.6526), SNP removed"],rs4803222:["chr19:39739353","G=0.747, C=0.253","SNP in LD with rs11322783 (R2=0.2703), SNP removed"],rs6508852:["chr19:39752262","A=0.263, G=0.737","SNP in LD with rs8101517 (R2=0.609), SNP removed"],rs66477315:["chr19:39751674","T=0.636, -=0.364","SNP in LD with rs8101517 (R2=0.1736), SNP removed"],rs688187:["chr19:39732752","G=0.465, A=0.535","SNP in LD with rs11322783 (R2=0.6682), SNP removed"],rs7248668:["chr19:39743821","G=0.924, A=0.076","SNP in LD with rs8099917 (R2=1.0), SNP removed"],rs74597329:["chr19:39739155","T=0.444, G=0.556","SNP in LD with rs11322783 (R2=1.0), SNP removed"],rs78605718:["chr19:39745812","C=0.904, T=0.096","SNP kept"],rs8099917:["chr19:39743165","T=0.924, G=0.076","SNP kept"],rs8101517:["chr19:39747741","A=0.328, C=0.672","SNP kept"],rs8103142:["chr19:39735106","T=0.424, C=0.576","SNP in LD with rs11322783 (R2=0.6), SNP removed"],rs8109886:["chr19:39742762","C=0.253, A=0.747","SNP in LD with rs11322783 (R2=0.4223), SNP removed"],rs955155:["chr19:39729479","G=0.96, A=0.04","SNP kept"]};
//var ldClipData = {warnings:[],details:[]};
var snpclipData = {"warnings":[{"rs_number":"rs12980602","position":"chr19:39752820","alleles":"T=0.763, C=0.237","comment":"SNP kept","rs_number_link":"<a>rs12980602</a>","position_link":"<a>chr19:39752820</a>"},{"rs_number":"rs35963157","position":"chr19:39745695","alleles":"-=0.338, C=0.662","comment":"SNP in LD with rs11322783 (R2=0.1887), SNP removed","rs_number_link":"<a>rs35963157</a>","position_link":"<a>chr19:39745695</a>"}],"details":[{"rs_number":"rs12980602","position":"chr19:39752820","alleles":"T=0.763, C=0.237","comment":"SNP kept","rs_number_link":"<a>rs12980602</a>","position_link":"<a>chr19:39752820</a>"},{"rs_number":"rs35963157","position":"chr19:39745695","alleles":"-=0.338, C=0.662","comment":"SNP in LD with rs11322783 (R2=0.1887), SNP removed","rs_number_link":"<a>rs35963157</a>","position_link":"<a>chr19:39745695</a>"}]};

//var snpchipData = {"snpchip":[{"rs_number":"rs505066","chromosome":"1","position":"96882671","map":["X","X","X","X","&nbsp;"]},{"rs_number":"rs505067","chromosome":"11","position":"74544780","map":["X","X","X","X","X"]}],"headers":["A_Hu-CHB","I_1M-D","I_1M","I_Exon510S","I_ME-Global-8"],"warning":"The following RS numbers were not found in dbSNP 142: rs1"};
//var snpchipData = {"snpchip":[{"rs_number":"<a href=\"http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=505066\" target=\"rs_number_rs505066\">rs505066</a>","chromosome":"1","position":"<a href=\"http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr1%3A96882421-96882921&snp142=pack&hgFind.matches=rs505066\" target=\"coord_chr1:96882671\">96882671</a>","map":["&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X","X","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;"]},{"rs_number":"<a href=\"http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=4478775\" target=\"rs_number_rs4478775\">rs4478775</a>","chromosome":"1","position":"<a href=\"http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr1%3A177769847-177770347&snp142=pack&hgFind.matches=rs4478775\" target=\"coord_chr1:177770097\">177770097</a>","map":["&nbsp;","X","&nbsp;","X","&nbsp;","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X","X","X","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X"]},{"rs_number":"<a href=\"http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=561634\" target=\"rs_number_rs561634\">rs561634</a>","chromosome":"1","position":"<a href=\"http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr1%3A177895513-177896013&snp142=pack&hgFind.matches=rs561634\" target=\"coord_chr1:177895763\">177895763</a>","map":["&nbsp;","X","&nbsp;","X","&nbsp;","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X","X","X","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X"]},{"rs_number":"<a href=\"http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=2820292\" target=\"rs_number_rs2820292\">rs2820292</a>","chromosome":"1","position":"<a href=\"http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr1%3A201784037-201784537&snp142=pack&hgFind.matches=rs2820292\" target=\"coord_chr1:201784287\">201784287</a>","map":["X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X"]}],"headers":["A_Hu-CHB","I_1M-D","I_1M","I_Exon510S","I_ME-Global-8"]};
var snpchipData = {"snpchip":[{"rs_number":"<a href=\"http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=505066\" target=\"rs_number_rs505066\">rs505066</a>","chromosome":"1","position":"<a href=\"http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr1%3A96882421-96882921&snp142=pack&hgFind.matches=rs505066\" target=\"coord_chr1:96882671\">96882671</a>","map":["&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X","X","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;"]},{"rs_number":"<a href=\"http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=4478775\" target=\"rs_number_rs4478775\">rs4478775</a>","chromosome":"1","position":"<a href=\"http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr1%3A177769847-177770347&snp142=pack&hgFind.matches=rs4478775\" target=\"coord_chr1:177770097\">177770097</a>","map":["&nbsp;","X","&nbsp;","X","&nbsp;","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X","X","X","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X"]},{"rs_number":"<a href=\"http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=561634\" target=\"rs_number_rs561634\">rs561634</a>","chromosome":"1","position":"<a href=\"http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr1%3A177895513-177896013&snp142=pack&hgFind.matches=rs561634\" target=\"coord_chr1:177895763\">177895763</a>","map":["&nbsp;","X","&nbsp;","X","&nbsp;","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X","X","X","X","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","&nbsp;","X"]},{"rs_number":"<a href=\"http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=2820292\" target=\"rs_number_rs2820292\">rs2820292</a>","chromosome":"1","position":"<a href=\"http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&position=chr1%3A201784037-201784537&snp142=pack&hgFind.matches=rs2820292\" target=\"coord_chr1:201784287\">201784287</a>","map":["X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X","X"]}],"headers":[{"code":"A_AFR","platform":"Affymetrix Axiom GW AFR"},{"code":"A_ASI","platform":"Affymetrix Axiom GW ASI"},{"code":"A_EAS","platform":"Affymetrix Axiom GW EAS"},{"code":"A_EUR","platform":"Affymetrix Axiom GW EUR"},{"code":"A_Hu","platform":"Affymetrix Axiom GW Hu"},{"code":"A_Hu-CHB","platform":"Affymetrix Axiom GW Hu-CHB"},{"code":"A_LAT","platform":"Affymetrix Axiom GW LAT"},{"code":"A_Onco","platform":"Affymetrix OncoScan"},{"code":"A_OncoCNV","platform":"Affymetrix OncoScan CNV"},{"code":"A_SNP6.0","platform":"Affymetrix SNP 6.0"},{"code":"I_CardioMetab","platform":"Illumina Cardio-MetaboChip"},{"code":"I_1M-D","platform":"Illumina Human1M-Duov3"},{"code":"I_1M","platform":"Illumina Human1Mv1"},{"code":"I_Exon510S","platform":"Illumina HumanExon510Sv1"},{"code":"I_O1S-8","platform":"Illumina HumanOmni1S-8v1"},{"code":"I_O2.5-4","platform":"Illumina HumanOmni2.5-4v1"},{"code":"I_O2.5-8","platform":"Illumina HumanOmni2.5-8v1.2"},{"code":"I_O2.5E-8v1","platform":"Illumina HumanOmni2.5Exome-8v1"},{"code":"I_O2.5E-8v1.1","platform":"Illumina HumanOmni2.5Exome-8v1.1"},{"code":"I_O2.5E-8v1.2","platform":"Illumina HumanOmni2.5Exome-8v1.2"},{"code":"I_O5-4","platform":"Illumina HumanOmni5-4v1"},{"code":"I_O5E-4","platform":"Illumina HumanOmni5Exome-4v1"},{"code":"I_ME-Global-8","platform":"Illumina Infinium Multi-Ethnic Global-8"}]};

var snpchipReverseLookup = [];
var ldClipRaw;
var modules = [ "ldhap", "ldmatrix", "ldpair", "ldproxy", "snpclip", "snpchip" ];

Object.size = function(obj) {
    var size = 0, key;
    for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};

$(document).ready(function() {

	updateVersion(ldlink_version);
	//addValidators();
	$('#ldlink-tabs').on('click', 'a', function(e) {
		var currentTab = e.target.id.substr(0, e.target.id.search('-'));
		window.history.pushState({},'', "?tab="+currentTab);
	});
	setupSNPclipControls();
	setupSNPchipControls();
	showFFWarning();

	var ldproxyTable = $('#new-ldproxy').DataTable( {
		"bPaginate": true,
		"bJQueryUI": false,  // ThemeRoller
		"bLengthChange": true,
		"bFilter": true,
		"bSort": true,
		"bInfo": true,
		"bAutoWidth": true,
		"bProcessing": false,
		"deferRender": false,
		"order": [[ 7, "desc" ], [ 5, "desc"]], //Order desc on DPrime
		"columnDefs": [
			{
				"render": function ( data, type, row ) {
					return ldproxy_rs_results_link(data, type, row);
				},
				"targets": 0
			},
			{
				"render": function ( data, type, row ) {
					//Remove 'chr' from the chromosome
					return data.substring(3);
				},
				"targets": 1
			},
			{
				"render": function ( data, type, row ) {
					return ldproxy_position_link(data, type, row);
				},
				"targets": 2
			},
			{
				"render": function ( data, type, row ) {
					return ldproxy_regulome_link(data, type, row);
				},
				"targets": 9
			},
			{
				"render": function ( data, type, row ) {
					return ldproxy_haploreg_link(data, type, row);
				},
				"targets": 10
			},
			{ className: "dt-body-center", "targets": [ 1, 9, 10 ] }
        ]
	});

	var new_proxy_data = {"aaData": [["rs125","chr7","24958977","(C/T)","0.2037",-726,"1.0","1.0","C-C,T-T","7","HaploReg link","NA"],["rs128","chr7","24958977","(C/T)","0.2037",-726,"1.0","1.0","C-C,T-T","7","HaploReg link","NA"],[".","chr4","24958977","(C/T)","0.2037",-726,"1.0","1.0","C-C,T-T","7","HaploReg link","NA"]]};
	RefreshTable('#new-ldproxy', new_proxy_data);
	
	$('[data-toggle="popover"]').popover();
	loadHelp();
	// Apply Bindings
	ko.applyBindings(ldpairModel, document
			.getElementById('ldpair-results-container'));
	//ko.applyBindings(ldproxyModel, document
	//		.getElementById('ldproxy-results-container'));
	ko.applyBindings(ldhapModel, document
			.getElementById('ldhap-results-container'));
	ko.applyBindings(snpclipModel, document
			.getElementById('snpclip-results-container'));

	ko.applyBindings(snpchipModel, document
			.getElementById('snpchip-results-container'));

	$.each(modules, function(key, id) {
		buildPopulationDropdown(id + "-population-codes");
		$("#"+ id + "-results-container").hide();
		$('#'+ id + '-message').hide();
		$('#'+ id + '-message-warning').hide();
		$('#'+ id + "-loading").hide();
	});

	$('.ldlinkForm').on('submit', function(e) {
		calculate(e);
	});

	// Add file select file listener
	$('.btn-file :file').on(
		'fileselect',
		function(event, numFiles, label) {
			populateTextArea(event, numFiles, label);
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

	$("body").keypress(function(e) {
		// Look for a return value
		var code = e.keyCode || e.which;
		if (code == 13) { // User pressed return key
		//	alert("You pressed return");
			// make sure focus is not in a textarea. If so ignore.
			var event_id = e.target.id;
			// Skip if you can't get event_id
			if (event_id === "") {

			} else {
				// Skip if user is editing TEXTAREA
				var tag_name = $("#" + event_id).get(0).tagName;
				if (tag_name == "TEXTAREA") {
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
			if (id.length == 2) { // Check to make sure we are on a
				// calculate
				// tab
				// check if the form is valid before sending to server
				var formId = id[0] + "Form";
				if ($('#' + formId).checkValidity) {
					initCalculate(id[0]);
					updateData(id[0]);
				}
			}
		}
	});

	setupTabs();
	autoCalculate();
});

// Set file support trigger
$(document).on(
	'change',
	'.btn-file :file',
	function() {
		var input = $(this), numFiles = input.get(0).files ? input
			.get(0).files.length : 1, label = input.val()
			.replace(/\\/g, '/').replace(/.*\//, '');
		input.trigger('fileselect', [ numFiles, label ]);
	}
);

function setupTabs() {
	//Clear the active tab on a reload
	$.each(modules, function(key, id) {
		$("#"+id+"-tab-anchor").removeClass('active');
	});
	$("#home-tab-anchor").removeClass('active');
	$("#help-tab-anchor").removeClass('active');
	//Look for a tab variable on the url
	var url = "{tab:''}";
	var search = location.search.substring(1);
	if(search.length >0 ) {
		url = JSON.parse('{"' + decodeURI(search).replace(/"/g, '\\"').replace(/&/g, '","').replace(/=/g,'":"').replace(/\n/, '\\\\n').replace(/\t/, '') + '"}');
	}

	var currentTab;
	if(typeof url.tab !="undefined") {
		currentTab = url.tab.toLowerCase();
	} else {
		currentTab = 'home';
	}

	if(currentTab.search('hap')>=0) currentTab = 'ldhap';
	if(currentTab.search('matrix')>=0) currentTab = 'ldmatrix';
	if(currentTab.search('pair')>=0) currentTab = 'ldpair';
	if(currentTab.search('proxy')>=0) currentTab = 'ldproxy';
	if(currentTab.search('clip')>=0) currentTab = 'snpclip';
	if(currentTab.search('chip')>=0) currentTab = 'snpchip';

	$('#'+currentTab+'-tab').addClass("in").addClass('active');
	$('#'+currentTab+'-tab-anchor').parent().addClass('active');

	if(typeof url.inputs !="undefined") {
		console.dir(url.inputs.replace(/\t/, '').replace(/\n/, '\\\\n'));
		updateData(currentTab, url.inputs.replace(/\t/, '').replace(/\n/, '\\\\n'));
	}

}

function refreshPopulation(pop, id) {

	$.each(pop, function(key, value){
		$('option[value="'+value+'"]', $('#'+id+'-population-codes')).prop('selected', true);
	});
	$('#'+id+'-population-codes').multiselect('refresh');

}

function autoCalculate() {
	// if valid parameters exist in the url then calcluate
	var url = {};
	var search = location.search.substring(1);
	if(search.length >0 ) {
		url = JSON.parse('{"' + decodeURI(search).replace(/"/g, '\\"').replace(/&/g, '","').replace(/=/g,'":"').replace(/\n/, '\\\\n').replace(/\t/, '') + '"}');
	}
	if(typeof url.tab !="undefined") {
	} else {
		return;
	}
	var id = url.tab.toLowerCase(); 
	switch (id) {
		case "ldpair":
			if(url.snp1 && url.snp2 && url.pop) {
				$("#ldpair-snp1").prop('value', url.snp1);
				$("#ldpair-snp2").prop('value', url.snp2);
				refreshPopulation(decodeURIComponent(url.pop).split("+"), id);
				initCalculate(id);
				updateData(id);
			}
			break;
		case "ldproxy":
			if(url.snp && url.pop && url.r2_d) {
				$("#ldproxy-snp").prop('value', url.snp);
				$("#proxy_color_r2").toggleClass('active', url.r2_d == "r2");
				$("#proxy_color_r2").next().toggleClass('active', url.r2_d == "d");
				refreshPopulation(decodeURIComponent(url.pop).split("+"), id);
				initCalculate(id);
				updateData(id);
			}
			break;
	} 
}

function setupSNPchipControls() {
	// Setup click listners for the platform selector
	$('#accordion').on('hidden.bs.collapse', toggleChevron);
	$('#accordion').on('shown.bs.collapse', toggleChevron);

	$('#selectAllChipTypes').click(function(e) {
		if($(".illumina:checked").length == $("input.illumina").length &&
			$(".affymetrix:checked").length == $("input.affymetrix").length) {
			$(".illumina").prop("checked", false);
			$(".affymetrix").prop("checked", false);
			$("#selectAllIllumina").prop("checked", false);
			$("#selectAllAffymetrix").prop("checked", false);
		} else {
			$(".illumina").prop("checked", true);
			$(".affymetrix").prop("checked", true);
			$("#selectAllIllumina").prop("checked", true);
			$("#selectAllAffymetrix").prop("checked", true);
		}
		checkSelectAllCheckbox();
		calculateChipTotals();
	});

	$('#selectAllIllumina').click(function(e) {
		var id = e.target.id;
		console.log("Look for state");
		//console.dir(e);
		console.log($("#"+id).prop('checked'));
		if($("#"+id).prop('checked') == true) {
			$(".illumina").prop("checked", true);
		} else {
			$(".illumina").prop("checked", false);
		}
		checkSelectAllCheckbox();
		calculateChipTotals();
	});
	$('#selectAllAffymetrix').click(function(e) {
		var id = e.target.id;
		if($("#"+id).prop('checked') == true) {
			$(".affymetrix").prop("checked", true);
		} else {
			$(".affymetrix").prop("checked", false);
		}
		checkSelectAllCheckbox();
		calculateChipTotals();
	});
	$('#collapseThree').on('click', "input.illumina, input.affymetrix", function(e) {
		checkSelectAllCheckbox();
		calculateChipTotals();
	});
	initChip();
}

function checkSelectAllCheckbox() {
	//Determin if the master checkbox should be checked or not.
	var illumina = $(".illumina:checked").length;
	var affymetrix = $(".affymetrix:checked").length;
	var total_illumina = $("input.illumina").length;
	var total_affymetrix = $("input.affymetrix").length;

	if(illumina == total_illumina) {
		$('#selectAllIllumina').prop('checked', true);
	} else {
		$('#selectAllIllumina').prop('checked', false);
	}
	if(affymetrix == total_affymetrix) {
		$('#selectAllAffymetrix').prop('checked', true);
	} else {
		$('#selectAllAffymetrix').prop('checked', false);
	}

	if(illumina == total_illumina && affymetrix == total_affymetrix) {
		$('#selectAllChipTypes').text("unselect all");
	} else {
		$('#selectAllChipTypes').text("select all");
	}

}

function calculateChipTotals() {
	
	var illumina = $(".illumina:checked").length;
	var affymetrix = $(".affymetrix:checked").length;

	$('#illumina-count').text(illumina);
	$('#affymetrix-count').text(affymetrix);
	if(illumina == 0 && affymetrix == 0) {
		$("#snpchip").prop('disabled', true);
	} else {
		$("#snpchip").prop('disabled', false);
	}

}

function setupSNPclipControls() {
	//('#snpclip').attr('disabled', false); // Remove this. (only need for testing)
	$('#snpclip-snp-list').on('click', "a", function(e) {
		//console.log("clicking on link");
		var rs_number = e.target.id;
		$('#snpclip-snp-list').show();
		$('#snpclip-initial-message').hide();
		loadSNPdetails(ldClipRaw, rs_number);
		$('#snpclip-details').show();
		$('#snpclip-warnings').hide();
		$('#snpclip-initial-message').hide();
	});
	$('#snpclip-warnings-button').click( function() {
		$('#snpclip-details').hide();
		$('#snpclip-initial-message').hide();
		$('#snpclip-warnings').show();
	});
}

function pushInputs(currentTab, inputs) {
	window.history.pushState({},'', "?tab="+currentTab+"&inputs="+JSON.stringify(inputs));
}

function showFFWarning() {
	// Is this a version of Mozilla?
	if ($.browser.mozilla) {
		var userAgent = navigator.userAgent.toLowerCase();
		// Is it Firefox?
		if (userAgent.indexOf('firefox') != -1) {
			userAgent = userAgent.substring(userAgent.indexOf('firefox/') + 8);
			var version = userAgent.substring(0, userAgent.indexOf('.'));
			if (version < 36) {
				$('.ffWarning').show();
			}
		}
	}
}

// Map knockout models to a sample json data
//var ldproxyModel = ko.mapping.fromJS(ldProxyData);
var ldpairModel = ko.mapping.fromJS(ldPairData);
var ldhapModel = ko.mapping.fromJS(ldhapData);
var snpclipModel = ko.mapping.fromJS(snpclipData);
var snpchipModel = ko.mapping.fromJS(snpchipData);

function RefreshTable(tableId, json) {
	table = $(tableId).dataTable();
	oSettings = table.fnSettings();
	table.fnClearTable(this);
	for (var i=0; i<json.aaData.length; i++) {
	  table.oApi._fnAddData(oSettings, json.aaData[i]);
	}
	oSettings.aiDisplay = oSettings.aiDisplayMaster.slice();
	table.fnDraw();
}



function ldproxy_rs_results_link(data, type, row) {


	//if no rs number is available return without a link.
	if(data.length == 1) {
		return "";
	}
	var server = 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi';
	var rs_number = data.substring(2);
	var params = {
		rs : rs_number
	};
	var href = server + "?" + $.param(params);
	var target = 'rs_number_' + Math.floor(Math.random() * (99999 - 10000 + 1));
//	var href = 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=128';
	var link;
	link = '<a href="'+href+'" target="'+target+'">'+data+'</a>';
	//return data +' ('+ row[3]+')';
	return link;
}

function ldproxy_position_link(data, type, row) {

	// Find the coord of the rs number
	//
	// Cluster Report:
	//
	var server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';
	// http://genome.ucsc.edu/cgi-bin/hgTracks?
	// position=chr4:103554686-104554686
	// &snp141=pack
	// &hgFind.matches=rs2720460
	// snp1-coord

	//
	// Genome Browser:
	//

	//var positions = data.query_snp.Coord.split(":");
	//Example:
	//http://genome.ucsc.edu/cgi-bin/hgTracks?position=chr7%3A24958727-24959227&snp141=pack&hgFind.matches=rs128
	var chr = row[1];
	var mid_value = parseInt(data);
	var offset = 250;
	var range = (mid_value - offset) + "-" + (mid_value + offset);
	var position = chr + ":" + range;
	var rs_number = row[0];
	var params = {
		db:'hg19',
		position : position,
		snp142 : 'pack',
		'hgFind.matches' : rs_number
	};
	var href = server + "?" + $.param(params);
	var target = 'position_' + Math.floor(Math.random() * (99999 - 10000 + 1));
	var link = '<a href="'+href+'" target="'+target+'">'+data+'</a>';

	return link;
}

function ldproxy_regulome_link(data, type, row ) {

	// Create RegulomeDB links

	var server = 'http://www.regulomedb.org/snp';
	var chr = row[1];
	var mid_value = parseInt(row[2]);
	var zero_base = mid_value - 1;
	var href = server + "/" + chr + "/" + zero_base;
	var target = 'regulome_' + Math.floor(Math.random() * (99999 - 10000 + 1));
	var link = '<a href="'+href+'" target="'+target+'">'+data+'</a>';

	return link;
}

function ldproxy_haploreg_link(data, type, row) {

	// Create RegulomeDB links

	var server = 'http://www.broadinstitute.org/mammals/haploreg/detail_v2.php';

	var rs_number = row[0];
	var params = {
		query : "",
		id : rs_number
	};
	var href = server + "?" + $.param(params);
	var target = 'haploreg_' + Math.floor(Math.random() * (99999 - 10000 + 1));
	var img = '<img src="LDproxy_external_link.png" alt="HaploReg Details" title="HaploReg Details" class="haploreg_external_link" style="width:16px;height:16px;">'; 
	var link = '<a href="'+href+'" target="'+target+'">'+img+'</a>';

	return link;

}

function updateVersion(version) {
	$("#ldlink_version").text(version);
}

function populateTextArea(event, numFiles, label) {
	id = event.target.id;
	if (window.FileReader) {

		var input = event.target;
		var reader = new FileReader();
		reader.onload = function() {
			var text = reader.result;
			$('#' + id + '-snp-numbers').val(text);
		};
		reader.readAsText(input.files[0]);
	} else {
		alert('FileReader not supported');
		return;
	}
}

function loadHelp() {
	$('#help-tab').load('help.html');
}


function calculate(e) {
	var formId = e.target.id;
	e.preventDefault();

/*
	var f = document.getElementsByTagName('form')[0];
	if(f.checkValidity()) {
		f.submit();
	} else {
		alert(document.getElementById('example').validationMessage);
	}
*/
	// var firstClick = $('#'+id+'-results-container').hasClass( "hidden" );

	// strip out "Form" from id
	var id = formId.slice(0, formId.length - 4);

	initCalculate(id);
	updateData(id);
}

function initCalculate(id) {
	$('#' + id + '-results-container').hide();
	$('#' + id + '-message').hide();
	$('#' + id + '-message-warning').hide();
}

function updateData(id) {

	$('#'+id+"-loading").show();

	switch (id) {
		case 'ldhap':
			updateLDhap();
			break;
		case 'ldmatrix':
			updateLDmatrix();
			break;
		case 'ldpair':
			updateLDpair();
			break;
		case 'ldproxy':
			updateLDproxy();
			break;
		case 'snpclip':
			updateSNPclip();
			break;
		case 'snpchip':
			updateSNPchip();
			break;
	}
}

function updateLDhap() {

	var id = "ldhap";

	var $btn = $('#' + id).button('loading');
	var snps = DOMPurify.sanitize($('#' + id + '-file-snp-numbers').val());
	var population = getPopulationCodes(id+'-population-codes');
	var ldInputs = {
		snps : snps,
		pop : population.join("+"),
		reference : Math.floor(Math.random() * (99999 - 10000 + 1))
	};
	var url = restServerUrl + "/ldhap";
	var ajaxRequest = $.ajax({
		type : 'GET',
		url : url,
		data : ldInputs,
		contentType : 'application/json' // JSON
	});

	ajaxRequest.success(function(data) {
		//data is returned as a string representation of JSON instead of JSON obj
		var jsonObj=JSON.parse(data);
		if (displayError(id, jsonObj) == false) {
			//console.info("LDhap is here");
			//console.dir($.parseJSON(data));
			$('#' + id + '-results-container').show();
			$('#' + id + '-links-container').show();
			var ldhapTable = formatLDhapData($.parseJSON(data));
			$('#ldhap-haplotypes-column').attr('colspan',
					ldhapTable.footer.length);

			ko.mapping.fromJS(ldhapTable, ldhapModel);

			addLDHapHyperLinks(ldInputs.reference, ldhapTable);
		}
	});
	ajaxRequest
			.fail(function(jqXHR, textStatus) {
				console.log("header: "
								+ jqXHR
								+ "\n"
								+ "Status: "
								+ textStatus
								+ "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
				// alert('Communication problem: ' + textStatus);
				// ERROR
				message = 'Service Unavailable: ' + textStatus + "<br>";
				message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

				$('#' + id + '-message').show();
				$('#' + id + '-message-content').empty().append(message);
				$('#' + id + '-progress').hide();
				$('#' + id+ '-results-container').hide();
				//hide loading icon
				$('#'+id+"-loading").hide();
			});
	ajaxRequest.always(function() {
		$btn.button('reset');
	});

	hideLoadingIcon(ajaxRequest, id);
}
function explodeLegalArray(entities) {
	//Turn an arry into a legal statement to use in a scentense
	//Example: array("Maryland", "New York", "Virginia")
	// = "Maryland, New York, and Virgina"

	var delimiter = ",";
	var output;
	if(entities.length == 0) {
		return entities[0];
	}

	$.each(entities, function (key, value) {
		if(key == 0) {
			output = value;
		} else if(key == entities.length-1) {
			output += " & "+value;
		} else {
			output += delimiter+" "+value;
		}
	});

	return output;
}

function updateSNPclip() {
	var id = "snpclip";

	var $btn = $('#' + id).button('loading');
	var snps = DOMPurify.sanitize($('#' + id + '-file-snp-numbers').val());
	var population = getPopulationCodes(id+'-population-codes');

	var ldInputs = {
		snps : snps,
		pop : population.join("+"),
		r2_threshold: $("#"+id+"_r2_threshold").val(),
		maf_threshold: $("#"+id+"_maf_threshold").val(),
		reference : Math.floor(Math.random() * (99999 - 10000 + 1))
	};
	//Show inital message
	$('#snpclip-details').hide();
	$('#snpclip-warnings').hide();
	$('#snpclip-initial-message').show();

	//Update href on
	//Set file links
	$("#snpclip-snps-link").attr('href', 'tmp/snp_list'+ldInputs.reference+'.txt');
	$("#snpclip-snps-link").attr('target', 'snp_thin_list_'+ldInputs.reference);
	$("#snpclip-details-link").attr('href', 'tmp/details'+ldInputs.reference+'.txt');
	$("#snpclip-details-link").attr('target', 'snp_details_'+ldInputs.reference);

	// Set populations on LDThinned
	$('.snpclip-populations').empty().append(explodeLegalArray(population));

	var url = restServerUrl + "/snpclip";
	var ajaxRequest = $.ajax({
		type : 'GET',
		url : url,
		data : ldInputs,
		contentType : 'application/json' // JSON
	});

	ajaxRequest.success(function(data) {
		//data is returned as a string representation of JSON instead of JSON obj
		var jsonObj=data;
		if (displayError(id, jsonObj) == false) {
			$('#' + id + '-results-container').show();
			$('#' + id + '-links-container').show();
			$('#'+id+"-loading").hide();
			initClip(data);
		}
	});
	ajaxRequest
			.fail(function(jqXHR, textStatus) {
				console.log("header: "
					+ jqXHR
					+ "\n"
					+ "Status: "
					+ textStatus
					+ "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
				message = 'Service Unavailable: ' + textStatus + "<br>";
				message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

				$('#' + id + '-message').show();
				$('#' + id + '-message-content').empty().append(message);
				$('#' + id + '-progress').hide();
				$('#' + id+ '-results-container').hide();
				//hide loading icon
				$('#'+id+"-loading").hide();
			});
	ajaxRequest.always(function() {
		$btn.button('reset');
	});

	hideLoadingIcon(ajaxRequest, id);
}

function updateSNPchip() {

	var id = "snpchip";

	var $btn = $('#' + id).button('loading');
	$("#collapseThree").removeClass("in");
	var snps = DOMPurify.sanitize($('#' + id + '-file-snp-numbers').val());
	var platforms = [];

	$('.affymetrix:checked').each(function() { 
		platforms.push($(this).val());
	});
	$('.illumina:checked').each(function() { 
		platforms.push($(this).val());
	});
	

	var ldInputs = {
		snps : snps,
		platforms: platforms.join("+"),
		reference : Math.floor(Math.random() * (99999 - 10000 + 1))
	};
	$('#snp_chip_list').attr('href', "tmp/details"+ldInputs.reference+".txt");
	$('#snp_chip_list').attr('target', "chip_details"+ldInputs.reference+".txt");
	//console.dir(ldInputs);
	var url = restServerUrl + "/snpchip";
	var ajaxRequest = $.ajax({
		type : 'GET',
		url : url,
		data : ldInputs,
		contentType : 'application/json' // JSON
	});

	ajaxRequest.success(function(data) {
		//data is returned as a string representation of JSON instead of JSON obj
		var jsonObj=data;
		if (displayError(id, jsonObj) == false) {
			$('#' + id + '-results-container').show();
			$('#' + id + '-links-container').show();
			$('#'+id+"-loading").hide();
			loadSNPChip(data);
		}
	});
	ajaxRequest.fail(function(jqXHR, textStatus) {
		console.log("header: "+jqXHR+"\n"+ "Status: "+ textStatus+ "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
		message = 'Service Unavailable: ' + textStatus + "<br>";
		message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

		$('#' + id + '-message').show();
		$('#' + id + '-message-content').empty().append(message);
		$('#' + id + '-progress').hide();
		$('#' + id+ '-results-container').hide();
		//hide loading icon
		$('#'+id+"-loading").hide();
	});
	ajaxRequest.always(function() {
		$btn.button('reset');
	});

	hideLoadingIcon(ajaxRequest, id);
}

function initChip() {
	//Setup the platform
	var id = "snpchip";

	var url = restServerUrl + "/snpchip_platforms";
	var ajaxRequest = $.ajax({
		type : 'GET',
		url : url,
		contentType : 'application/json' // JSON
	});

	ajaxRequest.success(function(data) {
		if (displayError(id, data) == false) {
			//buildPopulationDropdownSNPchip(data);
			buildPlatformSNPchip(data);
		}
	});
	ajaxRequest.fail(function(jqXHR, textStatus) {
		console.log("header: "+ jqXHR+ "\nStatus: "+textStatus+"\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
		message = 'Service Unavailable: ' + textStatus + "<br>";
		message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";
		message += "Unable to retrieve platform codes from the server."
		$('#' + id + '-message').show();
		$('#' + id + '-message-content').empty().append(message);
		$('#' + id + '-progress').hide();
		$('#' + id+ '-results-container').hide();
		//hide loading icon
		$('#'+id+"-loading").hide();
	});

}

function loadSNPChip(data) {
	//Setup data and display
	//snpchipData = [];
	// = "This is about error";

	delete snpchipData["warning"];
	delete snpchipData["error"];

	var snpchip = JSON.parse(data);
	var all_platforms_used = [];
	var newchip = [];
	var snpData;
	var obj;
	var test = "";
	var associated_platforms;

	$.each(snpchip, function(row, detail) {
		if(row.search("warning")>=0 ||row.search("error")>=0) {
			//Print the warning somewhere on the screen.
			if(row.search("warning")>=0) {
				snpchipData["warning"] = detail;
			}
			if(row.search("error")>=0) {
				snpchipData["error"] = detail;
			}
			//Remove this item
			delete snpchip[row];
		} else {
			//Gather all platforms
			//if(parseInt(row)< 1) {
				associated_platforms = detail[2].split(",");
				//console.log("associated_platforms: "+parseInt(row)+" "+detail[0]);
				//console.dir(associated_platforms.sort());

				$.each(detail[2].split(","), function(key, value){
					if(value != "") {
						all_platforms_used.push(value);
						test += key+") "+detail[2]+"\n";
					}
				});
			//}
		}
	});
	//console.warn("All Platforms");
	//console.log("Count: "+all_platforms_used.length);
	//Find the unique one from all of the platforms
	var used_platforms
	var platform_list = all_platforms_used.unique();
	var map = [];
	var reversed_platform_list = [];
	snpchipData["headers"] = [];
	platform_list.sort();
	//console.warn("Filtered list of  Platforms");
	//console.log("Count: "+platform_list.length);
	//console.log(test);

	//Now that we have the platform list... Map each platform.
	$.each(snpchip, function(row, detail){
		//Walk throught the platform_list and determine if it has the list... create a map for the table.
		map = [];
		used_platforms = detail[2].split(",");
		//console.log("used_platforms:");
		//console.dir(used_platforms);
		//console.warn("row: "+row);

		$.each(platform_list, function(key, value) {
			//console.log(key+":"+value);
			//console.info($.inArray(value, used_platforms));
			if($.inArray(value, used_platforms) >= 0) {
				map.push("X");
			} else {
				map.push("&nbsp;");
			}
		});
		//Split detail[1] into two parts
		var chromo_position = detail[1].split(":");
		obj = {
			"rs_number" : anchorRSnumber(detail[0]),
			"chromosome" : chromo_position[0],
			"position" : anchorRSposition("chr"+detail[1], detail[0], true),
			"map" : map
		};
		//console.dir(obj);
		newchip.push(obj);
	});

	$.each(platform_list, function(key, value) {
		//reversed_platform_list.push(snpchipReverseLookup[value]);

		obj ={
			code: snpchipReverseLookup[value],
			platform: value
		};
		if(typeof obj.code === "undefined") {
			console.info("Reverse lookup does appear to exist");
			console.info("Removing key "+key+" from platform_list below.");
			console.info("This value doesn't seem to have a code: "+value);
			console.log("platform_list:");
			console.dir(platform_list);
			obj ={
				code: "unknown code",
				platform: value
			};
			snpchipData["headers"].push(obj);
		} else {
			snpchipData["headers"].push(obj);
		}
	});
	snpchipData["snpchip"] = newchip;
	//Based on header size remove overflow-y
	//console.warn("Header size");
	//console.log(snpchipData["headers"].length);
	var header_len = snpchipData["headers"].length;
	if( header_len < 20) {
		//calcualte width
		$('#snpchip-table-right').attr('width', 100+(header_len*30));
	} else {
		$('#snpchip-table-right').removeAttr('width');
	}
	//$('#snpchip-table-right')...

	//snpchipData["headers"].push(= reversed_platform_list;
	//snpchipData["headers"].platform = platform_list;

	//snpchipData["headers"].code = reversed_platform_list;
	//snpchipData["headers"].platform = platform_list;

	// = "This is about error";
	//console.log("FINAL DATA HERE:");
	//console.dir(snpchipData);
	//console.log("FINAL DATA AS A STRING:");
	//console.log(JSON.stringify(snpchipData));
	ko.mapping.fromJS(snpchipData, snpchipModel);

	checkAlert("snpchip", snpchipData.warning, "warning", true);
	checkAlert("snpchip", snpchipData.error, "error", false);

}

function checkAlert(elementId, message, type, displayResults) {
	//type is either 'warning' or 'error'
	var prefix;
	if(type == 'warning') {
		prefix = elementId+'-message-warning';
	} else {
		prefix = elementId+'-message';
	}
	$('#'+prefix).hide();

	if (typeof message !== 'undefined' && message.length > 0) {
		$('#'+prefix+'-content').text(message);
		$('#'+prefix).show();
		if (typeof displayResults !== 'undefined' && displayResults) {
			$('#'+elementId+'-results-container').show();
		} else {
			$('#'+elementId+'-results-container').hide();
		}
	}
}

function populateSNPlist(data) {

	//clear out the list
	$("#snpclip-snp-list").empty();
	//Add the clipped list
	$.each(data.snp_list, function( index, value ){
		$("#snpclip-snp-list").append(
			$("<tr>").append(
				$("<td>").append(
					$("<a>")
						.attr('id', value)
						.attr('title', 'Click to view details')
						.append(value)
					)
				)
			)
	});

}

function anchorRSnumber(rs_number) {
	var server = 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi';

	var raw_rs_number = rs_number.substring(2);
	var params = {
		rs : raw_rs_number
	};
	var url = server + "?" + $.param(params);

	return '<a href="'+url+'" target="rs_number_'+rs_number+'">'+rs_number+'</a>';
}

function anchorRSposition(coord, rs_number, hide_chr) {
	//
	// Genome Browser:
	//
	hide_chr = hide_chr || false;

	if(coord.toUpperCase() == "NA")
		return "NA";

	server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';
	// snp1-coord
	var positions = coord.split(":");
	var chr = positions[0];
	var mid_value = parseInt(positions[1]);
	var offset = 250;
	var range = (mid_value - offset) + "-" + (mid_value + offset);
	var position = chr + ":" + range;
	params = {
		db:'hg19',
		position : position,
		snp142 : 'pack',
		'hgFind.matches' : rs_number
	};
	var url = server + "?" + $.param(params);
	if(hide_chr) {
		return '<a href="'+url+'" target="coord_'+coord+'">'+positions[1]+'</a>';
	} else {
		return '<a href="'+url+'" target="coord_'+coord+'">'+coord+'</a>';
	}
}

function populateSNPwarnings(data) {

	snpclipData.warnings = [];

	$.each(data.details, function( index, value ){

		var detail = {
			rs_number: index,
			position: value[0],
			alleles: value[1],
			comment: value[2],
			rs_number_link: anchorRSnumber(index),
			position_link: anchorRSposition(value[0], index)
		};
		console.log(index+" - "+value);
		if(detail.comment != 'SNP kept' && detail.comment.substring(0, 9) != 'SNP in LD') {
			// Place message on the warning table.
			snpclipData.warnings.push(detail);
		}
	});

	if(snpclipData.warnings.length == 0) {
		$('#snpclip-warning').hide();
	} else {
		$('#snpclip-warning').show();
	}
	ko.mapping.fromJS(snpclipData, snpclipModel);

}

function loadSNPdetails(data, rs_number) {

	snpclipData.details =[];

	console.log("Here is the rs_number to populate");
	console.log("rs_number: "+rs_number);
	//console.dir(data.details);
	console.log("find key for the rs_number");

	//console.log("Found one::::");
	//console.dir(data.details[rs_number]);

	var found = false;

	$.each(data.details, function( index, value ){
		var detail = {
			rs_number: index,
			position: value[0],
			alleles: value[1],
			comment: value[2],
			rs_number_link: anchorRSnumber(index),
			position_link: anchorRSposition(value[0], index)
		};
		console.log(index+" - "+value);
		if(detail.rs_number == rs_number) {
			found = true;
		}
		//if(found == true && detail.rs_number == rs_number) {
		if(found) {
			if(detail.comment == 'SNP kept' && detail.rs_number != rs_number){
				// List is complete, exit loop
				return false;
			}
			if(detail.comment == 'SNP kept' || detail.comment.substring(0, 9) =='SNP in LD') {
				snpclipData.details.push(detail);
			}
		}
	});
	console.dir(snpclipData);
	console.log(JSON.stringify(snpclipData));
	ko.mapping.fromJS(snpclipData, snpclipModel);
	$('#snpclip-detail-title').text("Details for "+rs_number); 
}

function initClip(data) {

	ldClipRaw = data;

	populateSNPwarnings(data);
	populateSNPlist(data);
	// Get first element
	if(data.snp_list.length == 0) {
		$('#snpclip-message-warning-content').text("SNPclip list returned no results for this calculation.");
		$('#snpclip-results-container').hide();
		$('#snpclip-message-warning').show();
	}
	//loadSNPdetails(data, rs_number);
	if(snpclipData.warnings.length == 0) {
		$('#snpclip-warnings-button').hide();
	} else {
		$('#snpclip-warnings-button').show();
	}

}

function formatLDhapData(data) {

	//console.info("LDhap Starts here:");
	//console.log('original data structure for ldhap:');
	//console.dir(data);

	//console.log("get the two main parts of the data as hplotypes and snps");
	//var indels = [];
	var haplotypes = data.haplotypes;

	//console.dir(haplotypes);

	var snps = data.snps;
	var ldhapTable = {
		footer : [],
		rows : []
	};
	//Get the indels from the haplotypes
	$.each( haplotypes, function( key, value ) {
		haplotypes[key].indels = value.Haplotype.split("_");
	});

	// Convert haplotypes to footer
	for (key in haplotypes) {
		//console.log(key);
		//console.dir(haplotypes[key]);
		var obj = {
			Count : haplotypes[key].Count,
			Frequency : haplotypes[key].Frequency,
			Haplotype : haplotypes[key].indels  
			/* Haplotype : ["A", "GGA", "-", 'G'] */ 
		};
		// Add Haplotypes with a frequency of 1% or greater.
		if (haplotypes[key].Frequency * 100 > 1) {
			ldhapTable.footer.push(obj);
		}
	}
	// Convert snps to rows.
	for (key in snps) {
		var obj = {
			Alleles : snps[key].Alleles,
			Coord : snps[key].Coord,
			RS : snps[key].RS,
			Haplotypes : []
		};
		ldhapTable.rows.push(obj);
	}
	// Add haplotypesHTML
	$.each(ldhapTable.rows, function(index, value) {
		// Get all the haplotypes in pivot order
		$.each(ldhapTable.footer, function(index2, value2) {

			value.Haplotypes[index2] = value2.Haplotype[index];

		});
	});

	//console.log('ldhapTable');
	//console.dir(ldhapTable);
	var obj = {
		out_final : ldhapTable
	}
	//console.dir(obj);
	//console.info("LDhap ENDS here:");

	return ldhapTable;
}

function updateLDmatrix() {
	var id = "ldmatrix";

	var $btn = $('#' + id).button('loading');

	var snps = DOMPurify.sanitize($('#' + id + '-file-snp-numbers').val());
	var population = getPopulationCodes(id+'-population-codes');
	var r2_d;

	if($('#matrix_color_r2').hasClass('active')) {
		r2_d='r2'; // i.e. R2
		$("#ldmatrix-legend").attr('src', 'LDmatrix_legend_R2.png');
	} else {
		r2_d='d';  // i.e.  Dprime
		$("#ldmatrix-legend").attr('src', 'LDmatrix_legend_Dprime.png');
	}

	var ldmatrixInputs = {
		snps : snps,
		pop : population.join("+"),
		reference : Math.floor(Math.random() * (99999 - 10000 + 1)),
		r2_d : r2_d
	};
	//console.log('ldmatrixInputs');
	//console.dir(ldmatrixInputs);

	var url = restServerUrl + "/ldmatrix";
	var ajaxRequest = $.ajax({
		type : 'GET',
		url : url,
		data : ldmatrixInputs
	});

	ajaxRequest.success(function(data) {
		$('#ldmatrix-bokeh-graph').empty().append(data);
		$('#' + id + '-progress-container').hide();
		$('#' + id + '-results-container').show();
		getLDmatrixResults(ldmatrixInputs.reference + ".json",
				ldmatrixInputs.reference);

	});
	ajaxRequest
			.fail(function(jqXHR, textStatus) {
				console
						.log("header: "
								+ jqXHR
								+ "\n"
								+ "Status: "
								+ textStatus
								+ "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
				// alert('Communication problem: ' + textStatus);
				// ERROR
				message = 'Service Unavailable: ' + textStatus + "<br>";
				message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

				$('#' + id + '-message').show();
				$('#' + id + '-message-content').empty().append(message);
				$('#' + id + '-progress').hide();
				$('#' + id+ '-results-container').hide();
				//hide loading icon
				$('#'+id+"-loading").hide();
			});
	ajaxRequest.always(function() {
		$btn.button('reset');
	});

	hideLoadingIcon(ajaxRequest, id);
}

function addLDMatrixHyperLinks(request) {
	$('#ldmatrix-DPrime').attr('href', 'tmp/d_prime_' + request + '.txt');
	$('#ldmatrix-R2').attr('href', 'tmp/r2_' + request + '.txt');
}
/*
function updateLDproxyProgressBar(id, seconds) {

	var milliseconds = seconds * 1000;
	// Divide number of milliseconds to get 100 to get 100 updates
	var delay = milliseconds / 100;

	$('#' + id + '-progress').show();
	var progressBar = $('#ldproxy-progress-bar');
	width = 0;

	progressBar.width(width);

	var interval = setInterval(function() {
		width += 1;
		progressBar.css('width', width + '%').attr('aria-valuenow',
				width.toString() + '%');
		progressBar.html('<span>' + width.toString() + '% Complete</span>');
		if (width >= 100) {
			clearInterval(interval);
			return;
		}
	}, delay);
}
*/
/*
function createPopulationDropdown(id) {

	alert("createPop");
	$('#' + id + '-population-codes')
		.multiselect(
		{
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
							+ this.nonSelectedText + '</span>'
							+ ' <b class="caret"></b>';
				} else if (options.length == $('option', $(select)).length) {
					return '<span class="pull-left">'
							+ this.nonSelectedText + '</span>'
							+ ' <b class="caret"></b>';
				} else if (options.length > this.numberDisplayed) {
					return '<span class="badge pull-left">'
							+ options.length + '</span> '
							+ this.nSelectedText
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
			},
			onChange : function(option, checked) {
				alert("You changed something");
            }
		});
}
*/

function updateLDproxy() {
	var id = "ldproxy";
	var $btn = $('#' + id).button('loading');
	var population = getPopulationCodes(id+'-population-codes');
	var r2_d;

	if($('#proxy_color_r2').hasClass('active')) {
		r2_d='r2'; // i.e. R2
		$('#ldproxy-genome').html("View R<sup>2</sup> data in UCSC Genome Browser");
		//$("#ldmatrix-legend").attr('src', 'LDmatrix_legend_R2.png');
	} else {
		r2_d='d';  // i.e.  Dprime
		$('#ldproxy-genome').html("View D' data in UCSC Genome Browser");
		//$("#ldmatrix-legend").attr('src', 'LDmatrix_legend_Dprime.png');
	}

	var ldproxyInputs = {
		snp : $('#ldproxy-snp').val(),
		pop : population.join("+"),
		reference : Math.floor(Math.random() * (99999 - 10000 + 1)),
		r2_d : r2_d
	};

	updateHistoryURL(id, ldproxyInputs);

	//console.log(location.hostname);

	$('#ldproxy-genome').attr('href',
		'http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg19&hgt.customText=http://'+location.hostname+'/LDlink/tmp/track' 
		+ ldproxyInputs.reference + '.txt');

	//console.dir(ldproxyInputs);
	$('#ldproxy-results-link').attr('href',
			'tmp/proxy' + ldproxyInputs.reference + '.txt');
	var url = restServerUrl + "/ldproxy";
	var ajaxRequest = $.ajax({
		type : "GET",
		url : url,
		data : ldproxyInputs
	});

	ajaxRequest.success(function(data) {
		$('#' + id + '-progress-container').hide();
		//Remove bokeh while testing.
		//$('#ldproxy-bokeh-graph').empty().append(data);
		$('#ldproxy-bokeh-graph').empty().append(data);
		$('#' + id + '-results-container').show();
		getLDProxyResults('proxy'+ldproxyInputs.reference+".json");

	});
	ajaxRequest
			.fail(function(jqXHR, textStatus) {
				console
						.log("header: "
								+ jqXHR
								+ "\n"
								+ "Status: "
								+ textStatus
								+ "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
				// alert('Communication problem: ' + textStatus);
				// ERROR
				message = 'Service Unavailable: ' + textStatus + "<br>";
				message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

				$('#' + id + '-message').show();
				$('#' + id + '-message-content').empty().append(message);
				$('#' + id + '-progress').hide();
				$('#' + id+ '-results-container').hide();
				//hide loading icon
				$('#'+id+"-loading").hide();
			});
	ajaxRequest.always(function() {
		$btn.button('reset');
	});

	//hideLoadingIcon(ajaxRequest, id);
}

function hideLoadingIcon(ajaxRequest, id) {
	ajaxRequest.done(function(msg) {
		//hide loading icon
		$('#'+id+"-loading").hide();
	});
}

function getLDProxyResults(jsonfile) {
	var id = "ldproxy";
	var url = "tmp/"+jsonfile;
	//console.info("Here is the LOG file");
	//console.log(url);

	var ajaxRequest = $.ajax({
		type : "GET",
		url : url
	});

	ajaxRequest.success(function(data) {
		//catch error and warning in json
		if (displayError(id, data) == false) {
			//console.info("Data from Proxy");
			//console.dir(data);
			RefreshTable('#new-ldproxy', data);
			//ko.mapping.fromJS(data, ldproxyModel);
			//addLDproxyHyperLinks(data);
		}

	});

	ajaxRequest.fail(function(jqXHR, textStatus) {
				// alert('Fail');
				console
						.log("header: "
								+ jqXHR
								+ "\n"
								+ "Status: "
								+ textStatus
								+ "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
				message = 'Service Unavailable: ' + textStatus + "<br>";
				message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

				$('#' + id + '-message').show();
				$('#' + id + '-message-content').empty().append(message);
				$('#' + id + '-progress').hide();
				$('#' + id+ '-results-container').hide();
				//hide loading icon
				$('#'+id+"-loading").hide();
			});
	ajaxRequest.always(function() {
	});
	hideLoadingIcon(ajaxRequest, id);
}

function getLDmatrixResults(jsonfile, request) {
	var id = "ldmatrix";
	var url = "tmp/matrix"+jsonfile;

	var ajaxRequest = $.ajax({
		type : "GET",
		url : url
	});

	ajaxRequest.success(function(data) {
		//catch error and warning in json
		if (displayError(id, data) == false) {
			addLDMatrixHyperLinks(request);
			//matrix specific
			$('#'+id+"-download-links").show();
		}
	});

	ajaxRequest
			.fail(function(jqXHR, textStatus) {
				// alert('Fail');
				console
						.log("header: "
								+ jqXHR
								+ "\n"
								+ "Status: "
								+ textStatus
								+ "\n\nThe server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.");
				message = 'Service Unavailable: ' + textStatus + "<br>";
				message += "The server is temporarily unable to service your request due to maintenance downtime or capacity problems. Please try again later.<br>";

				$('#' + id + '-message').show();
				$('#' + id + '-message-content').empty().append(message);
				$('#' + id + '-progress').hide();
				//hide loading icon
				$('#'+id+"-loading").hide();
			});
	ajaxRequest.always(function() {
	});
}

function updateHistoryURL(id, inputs) {
	//Update url with new vars
	var params = $.extend({}, inputs);
	delete params.reference;
	if(params.pop) {
		var population;
		var totalPopulations;
		population =  $('#'+id+'-population-codes').val();
		params.pop = population.join("+");
	}

	params["tab"] = id;
	var recursiveEncoded = $.param( params );
	window.history.pushState({},'', "?"+ recursiveEncoded);

	//console.log(JSON.stringify(params.pop));

}

function updateLDpair() {
	var id = 'ldpair';
	var $btn = $('#' + id).button('loading');

	var population = getPopulationCodes(id+'-population-codes');

	//console.log("LD Pair");
	//console.log('population');
	//console.dir(population);
	var ldpairInputs = {
		snp1 : $('#ldpair-snp1').val(),
		snp2 : $('#ldpair-snp2').val(),
		pop : population.join("+"),
		reference : "ref" + Math.floor(Math.random() * (99999 - 10000 + 1))
				+ 10000
	};

	updateHistoryURL(id, ldpairInputs);

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
			$('#' + id + '-results-container').show();
			addLDpairHyperLinks(data);
		}
	});
	ajaxRequest.fail(function(jqXHR, textStatus) {
		console.log("header: " + jqXHR + "\n" + "Status: " + textStatus
				+ "\n\nMake sure Flask Python server is available.");
		// alert('Communication problem: ' + textStatus);
		// ERROR
		$('#' + id + '-message').show();
		$('#' + id + '-message-content').empty().append(
				'Communication problem: ' + textStatus
						+ "<br>Make sure Flask Python server is available.");
		$('#' + id+ '-results-container').hide();
		//hide loading icon
		$('#'+id+"-loading").hide();
	});
	ajaxRequest.always(function() {
		$btn.button('reset');
	});
	hideLoadingIcon(ajaxRequest, id);
}

function displayError(id, data) {
	// Display error or warning if available.
	var error = false;
	if (data.warning) {
		$('#' + id + '-message-warning').show();
		$('#' + id + '-message-warning-content').empty().append(data.warning);
		//hide error
		$('#' + id + '-message').hide();
	}

	if (data.error) {
		// ERROR
		$('#' + id + '-message').show();
		$('#' + id + '-message-content').empty().append(data.error);
		//hide warning
		$('#' + id + '-message-warning').hide();

		//matrix specific
		$('#'+id+"-download-links").hide();

		$('#'+id+"-results-container").hide();

		error = true;
	}
	return error;
}

function addLDHapHyperLinks(request, ldhapTable) {
	$('#ldhap-snps').attr('href', 'tmp/snps_' + request + '.txt');
	$('#ldhap-haplotypes').attr('href', 'tmp/haplotypes_' + request + '.txt');

	var server;
	var params = {};
	var rs_number;
	var url;
	//server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';
	//console.log("ldhapData");
	

	$.each(ldhapTable.rows, function(index, value) {
		//console.log(index + ": " + value);
		// Create RSnumber link (Cluster Report)
		server = 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi';
		// snp1-rsum
		rs_number = value.RS.substring(2);
		params = {
			rs : rs_number
		};
		url = server + "?" + $.param(params);
		$('#RSnumber_hap_' + index + ' a:first-child').attr('href', url);

		// Create Coord link ()
		server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';
		positions = value.Coord.split(":");
		chr = positions[0];
		mid_value = parseInt(positions[1]);
		offset = 250;
		range = (mid_value - offset) + "-" + (mid_value + offset);
		position = chr + ":" + range;
		rs_number = value.RS;
		params = {
			db:'hg19',
			position : position,
			snp142 : 'pack',
			'hgFind.matches' : rs_number
		};
		url = server + "?" + $.param(params);
		$('#Coord_hap_' + index + ' a:first-child').attr('href', url);
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
	params = {
		rs : rs_number
	};
	url = server + "?" + $.param(params);
	$('#snp1-rsnum').attr('href', url)
	// snp2-rsum
	rs_number = data.snp2.rsnum.substring(2);
	params = {
		rs : rs_number
	};
	url = server + "?" + $.param(params);
	$('#snp2-rsnum').attr('href', url)
	//
	// Genome Browser:
	//
	server = 'http://genome.ucsc.edu/cgi-bin/hgTracks';
	// snp1-coord
	var positions = data.snp1.coord.split(":");
	var chr = positions[0];
	var mid_value = parseInt(positions[1]);
	var offset = 250;
	var range = (mid_value - offset) + "-" + (mid_value + offset);
	var position = chr + ":" + range;
	rs_number = data.snp1.rsnum;
	params = {
		db:'hg19',
		position : position,
		snp142 : 'pack',
		'hgFind.matches' : rs_number
	};
	url = server + "?" + $.param(params);
	$('#snp1-coord').attr('href', url)
	// snp2-coord
	positions = data.snp2.coord.split(":");
	chr = positions[0];
	mid_value = parseInt(positions[1]);
	offset = 250;
	range = (mid_value - offset) + "-" + (mid_value + offset);
	position = chr + ":" + range;
	rs_number = data.snp2.rsnum;
	params = {
		db:'hg19',
		position : position,
		snp142 : 'pack',
		'hgFind.matches' : rs_number
	};
	url = server + "?" + $.param(params);
	$('#snp2-coord').attr('href', url);

}
/*
function buildPopulationDropdownSNPchip(data) {

	//Change platforms to multiselect json

	var platforms = JSON.parse(data);
	var illumina = {};
	var affymetrix = {};
	$.each( platforms, function( code, description ) {
		if(description.search("Affymetrix") >= 0) {
			affymetrix[code] = description;
		}
		if(description.search("Illumina") >= 0) {
			illumina[code] = description;
		}
	});

	var elementId = 'snpchip-platform-list';
	var snpchip_platform_list = {
		"Affymetrix": affymetrix,
		"Illumina": illumina
	};

	$("#"+elementId).empty();
	$.each( snpchip_platform_list, function( group, platforms ) {
		//Add optgroup
		$("#"+elementId).append(
			$("<optgroup>")
				.attr('value', "("+group+") All "+group+" Arrays")
				.attr('label', "("+group+") All "+group+" Arrays")
				.attr('id', group)
		);
		$.each( platforms, function( key, value ) {
			$('#'+group).append(
				$("<option>")
					.attr('value', key)
					.text(value+" ("+key+")")
			);
		});
	});

	$('#' + elementId).multiselect({
		enableClickableOptGroups : true,
		buttonWidth : '210px',
		maxHeight : 500,
		buttonClass : 'btn btn-default btn-ldlink-multiselect',
		includeSelectAllOption : true,
		dropRight : false,
		allSelectedText : 'All Arrays',
		nonSelectedText : 'Select Arrays',
		numberDisplayed : 2,
		selectAllText : ' (ALL) All Arrays',
		previousOptionLength: 0,
		maxPopulationWarn: 2,
		maxPopulationWarnTimeout: 5000,
		maxPopulationWarnVisible: false,
		// buttonClass: 'btn btn-link',
		buttonText : function(options, select) {
			if(this.previousOptionLength < this.maxPopulationWarn && options.length >= this.maxPopulationWarn) {
				$('#'+elementId+'-popover').popover('show');
				this.maxPopulatinWarnVisible=true;
			}
			this.previousOptionLength = options.length;
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
*/

function addCheckBox(code, description, elementId, platform_class) {
	$("#"+elementId).append(
		$("<div>").append(
			$("<span>").addClass("platform-checkbox").append(
				$("<input>").attr('type','checkbox')
					.attr('id',code)
					.attr('value', code)
					.attr('checked', true)
					.addClass(platform_class)
				)
			).append(
			$("<span>").addClass("formw").append(
				$("<label>").attr('for',code)
					.css("font-weight", "normal")
					.text(description+" ("+code+")")
				)
			)
		);
}

function buildPlatformSNPchip(data) {

	//Change platforms to multiselect json
	/*
                   <div>
                       <span class="label">
                       	<input type="checkbox" value="I1" class="illuminaArray" name="arrayList[]" id="illumina1">
                       	</span>
                       <span class="formw">
                       	<label for="illumina1">Illumina Human-1 (I1)</label>
                       </span>
                   </div>

                   <div class="row">
                       <span class="label"><input type="checkbox" value="AAH" class="affymetrixArray" name="arrayList[]" id="affy12"></span>
                       <span class="formw"><label for="affy12">Affymetrix Axiom GW Hu Origins 1 (AAH)</label></span>
                   </div>

	*/

	var platforms = JSON.parse(data);
	var illumina = {};
	var affymetrix = {};
	snpchipReverseLookup =[];

	$.each(platforms, function( code, description ) {
		if(description.search("Affymetrix") >= 0) {
			affymetrix[code] = description;
			addCheckBox(code, description, "columnBcheckbox", "affymetrix");
		}
		if(description.search("Illumina") >= 0) {
			illumina[code] = description;
			addCheckBox(code, description, "columnAcheckbox", "illumina");
		}
		snpchipReverseLookup[description] = code;
	});

}

function buildPopulationDropdown(elementId) {

	var htmlText = "";
	var htmlText1 = "<optgroup value='ABBREV' label='(ABBREV) FULLNAME'>\n";
	var htmlText2 = "<option value='ABBREV'>(ABBREV) DETAIL </option>\n";
	for ( var popAbbrev in populations) {
		var population = populations[popAbbrev];
		htmlText += htmlText1
			.replace(/ABBREV/g, popAbbrev)
			.replace("FULLNAME", population.fullName);
		for ( var subPopAbbrev in population.subPopulations) {
			var subDetail = population.subPopulations[subPopAbbrev];
			htmlText += htmlText2
				.replace(/ABBREV/g, subPopAbbrev).replace("DETAIL", subDetail);
		}
		htmlText += "</optgroup>\n";
	}

	$('#' + elementId).html(htmlText);

	$('#' + elementId).multiselect({
		enableClickableOptGroups : true,
		buttonWidth : '180px',
		maxHeight : 500,
		buttonClass : 'btn btn-default btn-ldlink-multiselect',
		includeSelectAllOption : true,
		dropRight : false,
		allSelectedText : 'All Populations',
		nonSelectedText : 'Select Population',
		numberDisplayed : 4,
		selectAllText : ' (ALL) All Populations',
		previousOptionLength: 0,
		maxPopulationWarn: 2,
		maxPopulationWarnTimeout: 5000,
		maxPopulationWarnVisible: false,

		// buttonClass: 'btn btn-link',
		buttonText : function(options, select) {
			if(this.previousOptionLength < this.maxPopulationWarn && options.length >= this.maxPopulationWarn) {
				$('#'+elementId+'-popover').popover('show');
				this.maxPopulatinWarnVisible=true;
				setTimeout(function(){
					$('#'+elementId+'-popover').popover('destroy');
					this.maxPopulatinWarnVisible=false;
				}, this.maxPopulationWarnTimeout);
			} else {
				//Destory popover if it is currently being displayed.
				if(this.maxPopulatinWarnVisible) {
						$('#'+elementId+'-popover').popover('destroy');
				}
			}
			this.previousOptionLength = options.length;
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
		},
		onChange : function(option, checked) {
			/*
			var active_tab = $("#ldlink-tabs li:[class]='active']");
			console.dir(active_tab);
			*/
			//alert("You changed the population selection.");
			//console.log("Option: ")
			//console.dir(option[0]);
			//console.log("checked: ")
			//console.dir(checked);
		}
	});
}

function getPopulationCodes(id) {
	var population;
	var totalPopulations;
	population =  $('#'+id).val();
	totalPopulations = countSubPopulations(populations);
/*
	console.log("Populations (static)");
	console.log("Populations length: "+totalPopulations);

	console.dir(populations);
	console.log("Population selected");
	console.log("Population length: "+population.length);
*/
	//Check for selection of All
	// If total subPopulations equals number of population then popluation = array("All");
	if(totalPopulations == population.length) {
		//console.log("YOU SELECTED ALL.  CONGRATS!!!");
		population = ["ALL"];
		return population;
	}

	population = replaceSubGroups(population);

	return population;
}

function countSubPopulations(populations) {

	var totalPopulations = 0;
	var subPopulations;

	$.each(populations, function(i, val) {
		totalPopulations += Number(Object.size(val.subPopulations));
	});

	return totalPopulations;
}

function replaceSubGroups(population) {
	var totalGroupPopulations = 0;
	var subPopulationsFound = 0;
	var currentSubPopulations = [];
	//Determine if a group has all subPopulations selected.
	//console.dir(populations);
	$.each(populations, function(currentGroup, val) {
		totalGroupPopulations = Number(Object.size(val.subPopulations));
		subPopulationsFound = 0;
		currentSubPopulations = [];
		//console.info("currentGroup: "+currentGroup+ " ("+val.fullName+")");
		//console.log("Check all subPopulations in the currentGroup of "+currentGroup);
		//if there is one miss then abbondon effort
		$.each(val.subPopulations, function(pop, desc) {
			if($.inArray(pop, population) !== -1) {
				subPopulationsFound++;
				currentSubPopulations.push(pop);
				//console.log("pop found: "+pop);
			} else {
				missingPop = true;
				//console.log("pop missing: "+pop);
			}
		});
		if(currentSubPopulations.length == totalGroupPopulations) {
			//Remove populations of Group then add Group acronymn
			//console.warn("ADD This GROUP: "+currentGroup+"  ... all sub population were found for this group.");
			//console.log("BEFORE: "+population);
			//console.log("REMOVE THESE Populations:");
			//console.dir(currentSubPopulations);
			$.each(currentSubPopulations, function(key, value) {
				//Find position in array
				population.splice( $.inArray(value, population), 1 );
				//console.log("REMOVE: "+key+": "+value);
			});
			population.push(currentGroup);
			//console.dir(population);

		}
		//If all are found then 
		//totalPopulations += Number(Object.size(val.subPopulations));
	});

	return population;
}

function addValidators() {
	 $('#snpclipForm').formValidation({
        framework: 'bootstrap',
        icon: {
            valid: 'glyphicon glyphicon-ok',
            invalid: 'glyphicon glyphicon-remove',
            validating: 'glyphicon glyphicon-refresh'
        },
        fields: {
            price: {
                validators: {
                    notEmpty: {
                        message: 'The price is required'
                    },
                    numeric: {
                        message: 'The price must be a number'
                    }
                }
            },
            amount: {
                validators: {
                    notEmpty: {
                        message: 'The amount is required'
                    },
                    numeric: {
                        message: 'The amount must be a number'
                    }
                }
            },
            color: {
                validators: {
                    notEmpty: {
                        message: 'The color is required'
                    }
                }
            },
            size: {
                validators: {
                    notEmpty: {
                        message: 'The size is required'
                    }
                }
            }
        }
    });

}
/* Utilities */

function toggleChevron(e) {
    $(e.target)
        .prev('.panel-heading')
        .find("i.indicator")
        .toggleClass('glyphicon-chevron-down glyphicon-chevron-up');
}

Array.prototype.contains = function(v) {
    for(var i = 0; i < this.length; i++) {
        if(this[i] === v) return true;
    }
    return false;
};

Array.prototype.unique = function() {
    var arr = [];
    for(var i = 0; i < this.length; i++) {
        if(!arr.contains(this[i])) {
            arr.push(this[i]);
        }
    }
    return arr; 
}