console.log(winPercHistory);

new Chart(document.getElementById("winPercHistory"), {
    type: 'line',
    data: {
      labels: matchArr,
      datasets: [{
          data: Object.values(winPercHistory),
          borderColor: "#18d26e",
          label: "Win Percentage",
          fill: false
          },
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
                  suggestedMin: 0,
                  fontColor: "white",
                  fontSize: 14,
                  fontStyle: 'bold',
              }
          }],
          xAxes: [{
            gridLines: {
                color: 'white', 
                display: false, 
            },
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