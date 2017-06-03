d3.tsv("data/ipdata.tsv", function(error, failure) {
      if (error) return console.error(error);

      // Coerce data values to be numeric
      failure.forEach(function(d) {
        d3.keys(d).forEach(function(k){
          if(k === "year" || k ==="count"){
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
          .color("severity")
          .id(["severity","itemtype","procedure","site"])
          .depth(1)
          .size("count")
          .title("Finding Data")
          .time("year")
          .legend(true)
          .legend({
    	       "order": {
    	          "sort": "desc",
    	          "value": "size"}})
          .title({
             "total": true,
             "font":{"size":30}
          })
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
