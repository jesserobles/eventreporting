d3.tsv("data/systemscauses.tsv", function(error, failure) {
  if (error) return console.error(error);

  // Coerce data values to be numeric
  failure.forEach(function(d) {
    d3.keys(d).forEach(function(k){
      if(k != "unit_nme" && k != "name" && k != "causelevel"){
        d[k] = +d[k];
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
      .id(["name","causelevel"])
      .depth(0)
      .size("count")
      .title("System Failures")
      // .font({"size": 20})
      .title({
         "total": true,
         "font":{"size":30}
      })
      .color("count")
      .time("discoverydate")
      .labels({"align": "left", "valign": "top"})
      .legend(false)
      .messages(false)
      .resize(true)
      // .ui([
      //       {
      //         "label" : "View By",
      //         "method" : function(value, viz) {
      //           if (value === 'unit') {
      //             viz.id(["unit_nme","name"]).draw();
      //           }
      //           else {
      //             viz.id(["name","unit_nme"]).draw();
      //           }
      //         },
      //         "type" : "toggle",
      //         "value" : ["system", "unit"],
      //       },
      //       {
      //         "label" : "Filter",
      //         "method" : function(value, viz) {
      //           if (value === "all failures") {
      //             viz.data(allfailures)
      //               .draw();
      //           } else {
      //             viz.data(filtered)
      //               .draw();
      //           }
      //
      //         },
      //         "type" : "toggle",
      //         "value" : [, "all failures", "Inop/MRFF/AP-913"],
      //       }
      // ])
      // .ui({
      //        "position":"top",
      //        "align":"left",
      //        "font": {
      //                 "size":17,
      //                 "weight":"bold"
      //                }
      // })
      .draw()

}
// d3plus.textwrap()
//   .config({"resize": true})
