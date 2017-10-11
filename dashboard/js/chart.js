"use strict";
$.ready(init());
var charts;
var sliders;
function make_land_chart() {
    charts.landuse = Highcharts.chart("landuse_chart", {
      chart: {
         type: 'area'
      },
      title: {
         text: 'Land Use Classification (PREDICTS)'
      },
      subtitle: {
         text: 'Source: Land-use Harmonization Project (v2)'
      },
      xAxis: {
         //categories: [],
         tickmarkPlacement: 'on',
         title: {
	    enabled: false
         }
      },
      yAxis: {
         title: {
	    text: 'Percent'
         }
      },
      tooltip: {
         pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>{point.percentage:.1f}%</b>',
         split: true,
      },
      plotOptions: {
         area: {
	    stacking: 'percent',
	    //lineColor: '#ffffff',
	    lineWidth: 1,
	    marker: {
	       enabled: false,
	       lineWidth: 1,
	       lineColor: '#ffffff'
	    }
         }
      },
      series: [],
   });
}

function make_bii_chart() {
    charts.bii = Highcharts.chart("bii_chart", {
      chart: {
         type: 'line'
      },
      title: {
         text: 'BII Loss'
      },
      subtitle: {
         text: 'Source: PREDICTS & Land-use Harmonization Project (v2)'
      },
      xAxis: {
         //categories: [],
         tickmarkPlacement: 'on',
         title: {
	    enabled: false
         }
      },
      yAxis: {
         title: {
	    text: 'Relative to pristine landscape'
         },
	 minPadding: 0,
	 maxPadding: 0,
	 min: 0.75,
      },
      tooltip: {
         pointFormat: '<span style="color:{series.color}">{series.name}</span>:<b>{point.y:.3f}</b><br/>',
         shared: true,
	 crosshairs: true
      },
      plotOptions: {
         line: {
	    lineWidth: 2,
         },
	 marker: {
	    lineWidth: 2,
	 },
      },
      series: [],
   });
}

function make_pop_chart() {
    charts.pop = Highcharts.chart("pop_chart", {
      chart: {
         type: 'line'
      },
      title: {
         text: 'Human Population'
      },
      subtitle: {
         text: 'Source: Spatial Population Scenarios'
      },
      xAxis: {
         //categories: [],
         tickmarkPlacement: 'on',
         title: {
	    enabled: false
         }
      },
      yAxis: {
         title: {
	    text: 'Total'
         },
	 minPadding: 0,
	 maxPadding: 0,
      },
      tooltip: {
         pointFormat: '<span style="color:{series.color}">{series.name}</span>:<b>{point.y:.3f}</b> B<br/>',
         shared: true,
	 crosshairs: true
      },
      plotOptions: {
         line: {
	    lineWidth: 2,
         },
	 marker: {
	    lineWidth: 2,
	 },
      },
      series: [],
   });
}

function set_year_limits(scenario) {
   var max = 2010,
       min = 1950,
       val = $('#year-selector').val()
   if (scenario != "historical") {
      max = 2099;
      min = 2015;
   }
   if (val < min || val > max) {
      val = min + (max - min) / 2;
   }
   $('#year-selector').attr("max", max) .attr("min", min).val(val);
   return val;
}

function draw_bii_chart() {
   $.getJSON("../data/bii.json", function (data) {
      console.log("received BII data");
      charts.bii.xAxis[0].setCategories(data.years.map(String));
      for (var idx = 0; idx < data.data.length; idx++) {
	 charts.bii.addSeries({name: data.data[idx].name,
			       data: data.data[idx].data})
      }
   }).fail(function(jqXHR, textStatus, errorThrown) {
      alert("Error: " + textStatus + " errorThrown: " + errorThrown);
   });
}

function draw_pop_chart() {
   $.getJSON("../data/pop.json", function (data) {
      console.log("received POP data");
      charts.pop.xAxis[0].setCategories(data.years.map(String));
      for (var idx = 0; idx < data.data.length; idx++) {
	 charts.pop.addSeries({name: data.data[idx].name,
			       data: data.data[idx].data})
      }
   }).fail(function(jqXHR, textStatus, errorThrown) {
      alert("Error: " + textStatus + " errorThrown: " + errorThrown);
   });
}

function init() {
   charts = {};
   var year = $('#year-selector').val();
   var scenario = $('#scenario-selector').val();
   $('#year-selector').tooltip({title: function() {
      console.log("calling to get toottip title");
      return this.value;
   }}).on('input', function(x) {
      var tip = $(this).data('bs.tooltip').tip();
      $(tip).children('.tooltip-inner').text(this.value);
   });
   $('#year-selector').on('change', function (x) {
      redraw_bii_map();
   });
   $('#scenario-selector').on('change', function (x) {
      var scenario = $('#scenario-selector').val();
      var year = set_year_limits(scenario);
      console.log("loading scenario: " + scenario);
      redraw(scenario, year);
   });
   make_land_chart();
   make_bii_chart();
   make_pop_chart();
   draw_bii_chart();
   draw_pop_chart();
   redraw(scenario, year);
}

function redraw_bii_map(scenario, year) {
   if (scenario == null || scenario == "") {
      scenario = $('#scenario-selector').val();
   }
   if (year == null || year == "") {
      year = $('#year-selector').val();
   }
   $("#bii_map_wrap").hide();
   $("#bii-loader").show();
   var d = new Date();
   var img_path = "http://temporalbii.s3.amazonaws.com/ssp-proj/" +
       scenario + "-bii-" + year + ".png?" + d.getTime();
   console.log(img_path);
   $("#bii_map").attr("src", img_path);
   $("#bii_map_wrap").show();
   $("#bii-loader").hide();
   //$("#bii_map_wrap").html("<img src='" + img_path + "'>");
}

function redraw(scenario, year) {
   $.getJSON("../data/" + scenario + ".json", function (data) {
      console.log("received data");
      while(charts.landuse.series.length > 0) {
	 charts.landuse.series[0].remove(true);
      }
      charts.landuse.xAxis[0].setCategories(data.years.map(String));
      for (var idx = 0; idx < data.data.length; idx++) {
	 charts.landuse.addSeries({name: data.data[idx].name,
				   data: data.data[idx].data})
      }
   }).fail(function(jqXHR, textStatus, errorThrown) {
    alert("Error: " + textStatus + " errorThrown: " + errorThrown);
   });
   
   redraw_bii_map(scenario, year);
}
