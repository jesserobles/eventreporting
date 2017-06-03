trendingsystems = []
d3.tsv("data/trendingsystems.tsv", function(error, systems) {
  if (error) return console.error(error);
  systems.forEach(function(d) {
    trendingsystems.push(d['Systems'])
  })
});
