var xAxis = []
for (var i = 0; i < matchArr.length; i++) {
    xAxis.push(0);
}

new Chart(document.getElementById("profitHistory"), {
    type: 'line',
    data: {
      labels: matchArr,
      datasets: [{
          data: Object.values(profitTotals),
          borderColor: "#18d26e",
          label: "Profit (USD)",
          fill: false
          },
          {
            radius: 0,
            data: xAxis,
            label: 'Breakeven',
            borderColor: "white",
            fill: false
            
        }

       ]
    },
    scaleFontColor: "white",
    options: {
      scaleFontColor: "white",
      legend: {
          labels: {
              fontStyle: 'bold',

              fontColor: "white",
              fontSize: 18
          }
      },
      scales: {
          yAxes: [{
            gridLines: {
                color: 'white', 
                display: false, 
            },
              ticks: {
                  fontColor: "white",
                  fontSize: 14,
                  fontStyle: 'bold',
              }
          }],
          xAxes: [{
            
            scaleLabel: {
                display: true,
                fontStyle: 'bold',
                labelString: 'Bet Number',
                fontColor: 'white',
                fontSize: 20
            },
            ticks: {
                fontColor: "white",
                fontStyle: 'bold',
                fontSize: 14
            }
          }]
      }
    }
  });