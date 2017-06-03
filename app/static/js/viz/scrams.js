d3.tsv("data/scramssystems.tsv", function(error, failure) {
    if (error) return console.error(error);

    // Coerce data values to be numeric
    failure.forEach(function(d) {
      d3.keys(d).forEach(function(k){
        if(k != "name"){
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
        .id("name")
        .size("count")
        .title("Systems Tagged in Scrams")
        .title({
           "total": true,
           "font":{"size":30}
        })
        // .font({"size":20})
        .color("count")
        .time("discoverydate")
        .labels({"align": "left", "valign": "top"})
        .legend(false)
        .messages(false)
        .resize(true)
        .tooltip({"html":function(value) {
          value = findAndReplace(value, " ", "%20");
          html = "<iframe id=\"tooltip\" src=\"tooltip.html?sys=" + value + "\" width=\"100%\" height=\"100%\" frameborder=\"0\" overflow=\"hidden\"></iframe>"
          return html;
        }})
        .ui({
               "font": {
                        "size":17,
                        "weight":"bold"
                       }
        })
        .draw()
}


function findAndReplace(string, target, replacement) {
 var i = 0, length = string.length;
 for (i; i < length; i++) {
   string = string.replace(target, replacement);
 }
 return string;
}