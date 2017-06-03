var causes = [];
var causesObj = [];
d3.tsv("data/causetimeseries.tsv", function(error, failure) {
  if (error) return console.error(error);

  // Coerce data values to be numeric
  failure.forEach(function(d) {
    d3.keys(d).forEach(function(k){
      if(k != "discoverydate" && k != "causecategory"){
        d[k] = +d[k]
      }
      if (k === "causecategory"){
        if (!causes.includes(d[k])){
          causes.push(d[k]);
        }
      }
    })
  });
  causes.sort();
  causes.forEach(function(item, index) {
    //console.log(typeof(item));
    var singleObj = {}
    singleObj[item] = item;
    causesObj.push(singleObj);
  });
  make_viz(failure);
});

function make_viz(data){
  var visualization = d3plus.viz()
  .container("#viz")
  .data(data)
  .type("line")
  .font({"size": 15})
  .title(false)
  .id("causecategory")
  .id({"solo" : [causes[0]]})
  .x({"value":"discoverydate",
      "label":"Quarter"
  })
  .y({"value":"failures",
      "label":"Number of Failures",
  })
  .size(1)
  .shape("line")
  .resize(true)
  .messages(false)
  .ui([
    {
      "method" : function(value, viz){
        viz.id({"solo" : [value]}).draw();
      },
      "label" : "Cause",
      "type" : "drop",
      "value" : causesObj,
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
