var systems = [];
var systemsObj = [];
d3.tsv("data/timeseries.tsv", function(error, failure) {
  if (error) return console.error(error);

  // Coerce data values to be numeric
  failure.forEach(function(d) {
    d3.keys(d).forEach(function(k){
      if(k != "discoverydate" && k != "name"){
        d[k] = +d[k]
      }
      if (k === "name"){
        if (!systems.includes(d[k])){
          systems.push(d[k]);
        }
      }
    })
  });
  systems.sort();
   systems.forEach(function(item, index) {
     //console.log(typeof(item));
     var singleObj = {}
     singleObj[item] = item;
     systemsObj.push(singleObj);
   })
  make_viz(failure);
});

function make_viz(data){
  var visualization = d3plus.viz()
    .container("#viz")
    .data(data)
    .type("line")
    .font({"size": 14})
    .title(false)
    .id("name")
    .id({"solo" : [systems[0]]})
    .x({"value":"discoverydate",
        "label":"Quarter"
    })
    .y({"value":"count",
        "label":"Number of Failures"
    })
    .size(1)
    .shape("line")
    //   "interpolate" : "monotone",
    //   "rendering" : "crispEdges"
    // })
    .resize(true)
    .messages(false)
    .ui([
          {
            "method" : function(value, viz) {
                viz.id({"solo" : [value]}).draw();
            },
            "label" : "System",
            "type" : "drop",
            "value" : systemsObj,
          },
          {
            "method" : function(value, viz) {
              if (value === "bar") {
                viz.type(value).shape("square").draw();
              } else {
                viz.type(value).size(1).shape("line").draw();
              }


              },
            "label" : "Chart Type",
            "type" : "toggle",
            "value" : ["line", "bar"],
          }
        ])
    .ui({
           "position":"top",
           "font": {
                    "size":17,
                    "weight":"bold"
                   }
    })
    .draw()
}
