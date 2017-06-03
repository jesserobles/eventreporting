function getQueryVariable(variable)
{
       var query = window.location.search.substring(1);
       var vars = query.split("&");
       for (var i=0;i<vars.length;i++) {
               var pair = vars[i].split("=");
               if(pair[0] == variable){return findAndReplace(pair[1],"%20", " ");}
       }
       return(false);
}

function findAndReplace(string, target, replacement) {
 var i = 0, length = string.length;
 for (i; i < length; i++) {
   string = string.replace(target, replacement);
 }
 return string;
}

var systems = [];
var systemsObj = [];
d3.tsv("data/scramssystems.tsv", function(error, failure) {
  if (error) return console.error(error);

  // Coerce data values to be numeric
  failure.forEach(function(d) {
    d3.keys(d).forEach(function(k){
      if(k != "name"){
        d[k] = +d[k]
      }
      if(k==="discoverydate") {
        d["year"] = d[k];
      }
    })
  });
  system = getQueryVariable("sys");
  make_viz(failure, system);
});

function make_viz(data, sys){
  var visualization = d3plus.viz()
    .container("#viz")
    .data(data)
    .type("line")
    .title(false)
    .id("name")
    .id({"solo" : sys})
    .x({"value":"year",
        "grid":false,
        "axis":false,
        "ticks":false
    })
    .y({"value":"count",
        "label":"Number of Failures",
        "grid":false,
        "axis":false,
        "ticks":false
    })
    .shape("line")
    .size(1)
    .resize(true)
    .messages(false)
    .draw()
}