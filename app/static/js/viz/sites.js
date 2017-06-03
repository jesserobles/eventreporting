d3.tsv("data/tmapsitedata.tsv", function(error, failure) {
  if (error) return console.error(error);

  // Coerce data values to be numeric
  failure.forEach(function(d) {
    d3.keys(d).forEach(function(k){
      if(k != "name" && k != "region"){
        d[k] = +d[k]

      }
      if(k === "region") {
        d[k] = "R"+d[k]

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
      .id(["region","name"])
      .depth(1)
      .size("reports")
      .legend({
	       "order": {
	          "sort": "desc",
	          "value": "size"}})
      .title("Record Counts by Site (per unit)")
      // .font({"size": 20})
      .title({
         "total": true,
         "font":{"size" : 30}
      })
      .time("year")
      .labels({"align": "left", "valign": "top"})
      .messages(false)
      .resize(true)
      .ui({
             "font": {
                      "size":17,
                      "weight":"bold"
                     }
      })
      .draw()
}
