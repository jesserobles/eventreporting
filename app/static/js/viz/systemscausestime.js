var systems = [];
var causes = [];
var systemsObj = [];
var causesObj = [];
var tmp;
d3.tsv("data/systemscauses.tsv", function(error, failure) {
  if (error) return console.error(error);

  // Coerce data values to be numeric
  failure.forEach(function(d) {
    d3.keys(d).forEach(function(k){
      if(k != "unit_nme" && k != "name" && k != "causelevel"  && k != "causecategory"  && k != "causefactor"){
        d[k] = +d[k];
      }
      if (k === "name"){
        if (!systems.includes(d[k])){
          systems.push(d[k]);
        }
      }
      if (k === "causelevel"){
        if (!causes.includes(d[k])){
          causes.push(d[k]);
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
  });
  causes.forEach(function(item, index) {
    var singleObj = {}
    singleObj[item] = item;
    causesObj.push(singleObj);
  });
  tmp = failure;
  make_viz(failure);
});

function make_viz(data){
  var visualization = d3plus.viz()
    .container("#viz")
    .data(data)
    .depth(0)
    .type("bar")
    .font({"size": 14})
    // .title(false)
    .id(["name", "causelevel", "causecategory", "causefactor", "unit_nme"])
    .id({"solo" : [systems[0]]})
    .time("discoverydate")
    .x({"value":"discoverydate",
        "label":"Year"
    })
    .y({"value":"count",
        "label":"Cause Tag Counts*",
        // "ticks": {"labels": false}
    })
    .resize(true)
    .ui([
          {
            "method" : function(value, viz) {
                viz.id({"solo" : [value]}).draw();
            },
            "label" : "System",
            "type" : "drop",
            "value" : systemsObj,

          },
          // {
          //   "method" : function(value, viz) {
          //     if (value === "causes") {
          //       viz.depth(1)
          //         .draw();
          //     } else {
          //
          //       viz.depth(0)
          //         .draw();
          //     }
          //
          //
          //     },
          //   "label" : "Depth",
          //   "type" : "toggle",
          //   "value" : ["systems", "causes"],
          // }
        ])
    .ui({
           "position":"bottom",
           "font": {
                    "size":17,
                    "weight":"bold"
                   }
    })
    .draw()
}
