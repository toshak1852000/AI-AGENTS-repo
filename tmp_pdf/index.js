const fs = require('fs');
const pdf = require('pdf-parse');

let dataBuffer = fs.readFileSync('D:/Stradit_AI/PortfoliQ/portfolioq/Digital Worker Resume 5.pdf');

pdf(dataBuffer).then(function (data) {
    console.log(data.text);
}).catch(function (error) {
    console.error(error);
});
