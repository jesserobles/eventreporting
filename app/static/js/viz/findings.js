d3.tsv("data/findings.tsv", function(error, failure) {
      if (error) return console.error(error);

      // Coerce data values to be numeric
      failure.forEach(function(d) {
        d3.keys(d).forEach(function(k){
          if(k != "region" && k != "site" && k != "type" && k != "severity" && k != "cornerstone"){
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
          .color("region")
          .id(["region","site", "severity", "cornerstone"])
          .depth(1)
          .size("freq")
          .title("Findings (Demo)")
          .title({
             "total": true,
             "font":{"size":30}
          })
          .time({"value": "year", "solo": 2015})
          .messages(false)
          .labels({"align": "left", "valign": "top"})
          .resize(true)
          .legend({
    	       "order": {
    	          "sort": "desc",
    	          "value": "size"}})
          .draw()
    }
