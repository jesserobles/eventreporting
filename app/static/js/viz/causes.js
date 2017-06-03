d3.tsv("data/allcauselevels.tsv", function(error, failure) {
      if (error) return console.error(error);

      // Coerce data values to be numeric
      failure.forEach(function(d) {
        d3.keys(d).forEach(function(k){
          if(k != "causelevel" && k != "causecategory" && k != "causefactor" && k != "unit"){
            d[k] = +d[k]
          }
        })
      });

      make_viz(failure);
    });

    function make_viz(data){
      var visualization = d3plus.viz()
          .container("#viz")
          .data(data)
          .type("tree_map")
          .color("causelevel")
          .id(["causelevel","causecategory","causefactor","unit"])
          .depth(1)
          .size("freq")
          .title("Failure Causes")
          .title({
             "total": true,
             "font":{"size":30}
          })
          .time("discoverydate")
          .messages({"branding": true})
          .labels({"align": "left", "valign": "top"})
          .resize(true)
          .ui([
            {
              "label" : "View By",
              "method" : function(value, viz) {
                if (value === 'unit') {
                  viz.id(["unit","causelevel","causecategory","causefactor"]).depth(0).color("freq").legend(false).draw();
                }
                else {
                  viz.id(["causelevel","causecategory","causefactor","unit"]).color("causelevel").depth(1).legend(true).draw();
                }
              },
              "type" : "toggle",
              "value" : ["cause", "unit"],
            }
          ])
          .ui({
                 "position":"top",
                 "align":"left",
                 "font": {
                          "size":17,
                          "weight":"bold"
                         }
          })
          .draw()
    }
