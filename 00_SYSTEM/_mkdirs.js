const fs = require('fs');
const dirs = ['sentinel','inquisitor','shared','db','tests'];
dirs.forEach(d => fs.mkdirSync(`C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\autonomos\\${d}`, {recursive: true}));
console.log('DONE');
