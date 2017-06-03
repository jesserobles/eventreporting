
function getParameterByName(url) {
    if (!url) {
      url = window.location.href;
    }
    var system = url.substr(url.lastIndexOf('/') + 1)
    return decodeURIComponent(system.replace(/\+/g, " ")).replace('.html', '') + '.tsv';
}
file = getParameterByName();
title = (file.replace('irs', '')[0].toUpperCase() + file.replace('irs', '').substr(1)).replace('.tsv', '')
d3.tsv("data/" + file, function(error, failure) {
  if (error) return console.error(error);

  // Coerce data values to be numeric
  failure.forEach(function(d) {
    d3.keys(d).forEach(function(k){
      if(k != "name" && k != "unit_nme" && k != "category"){
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
      .color("category")
      .id(["category", "name", "unit_nme"])
      .depth(1)
      .size("count")
      .title("IAEA Incident Reporting System (IRS) " + title)
      .title({
         "total": true,
         "font":{"size":30}
      })
      .time({"value": "discoverydate", "solo": [2012, 2013, 2014, 2015, 2016]})
      .labels({"align": "left", "valign": "top"})
      .legend({
	       "order": {
	          "sort": "desc",
	          "value": "size"}})
      .messages(false)
      .resize(true)
      .ui([
            {
              "label" : "View By",
              "method" : function(value, viz) {
                if (value === 'country') {
                  viz.id(["unit_nme","category", "name"]).depth(0).color("count").legend(false).draw();
                }
                else {
                  viz.id(["category", "name", "unit_nme"])
                    .color("category")
                    .depth(1)
                    .legend(true)
                    .legend({
                            "order": {
                                "sort": "desc",
                                "value": "size"}})
                    .draw();
                }
              },
              "type" : "toggle",
              "value" : ["system", "country"],
            },
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
