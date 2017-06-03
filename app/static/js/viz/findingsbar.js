var types = [];
var typesObj = [];
d3.tsv("data/bardata.tsv", function(error, failure) {
      if (error) return console.error(error);

      // Coerce data values to be numeric
      failure.forEach(function(d) {
        d3.keys(d).forEach(function(k){
          if(k != "type"){
            d[k] = +d[k]
          }
          if (k === "type"){
            if (!types.includes(d[k])){
              types.push(d[k]);
            }
          }
        })
      });
      types.sort();
      types.forEach(function(item, index) {
        //console.log(typeof(item));
        var singleObj = {}
        singleObj[item] = item;
        typesObj.push(singleObj);
      });
      make_viz(failure);
    });

    function make_viz(data){
      var visualization = d3plus.viz()
        .container("#viz")
        .data(data)
        .type("bar")
        .font({"size": 15})
        .title(false)
        .id("type")
        .id({"solo" : types[0]})
        .x("year")
        .y({"value": "freq",
            "label": "Counts"})
        // .size(1)
        .resize(true)
        .messages(false)
        .ui([
          {
            "method" : function(value, viz){
              viz.id({"solo" : [value]}).draw();
            },
            "label" : "Type",
            "type" : "drop",
            "value" : typesObj,
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
            "value" : ["bar", "line"],
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
