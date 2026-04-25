const fs = require('fs');
const html = fs.readFileSync('static/index.html', 'utf-8');
const js = fs.readFileSync('static/script.js', 'utf-8');

const idRegex = /id="([^"]+)"/g;
let match;
const ids = new Set();
while ((match = idRegex.exec(html)) !== null) {
    ids.add(match[1]);
}

const getElementByIdRegex = /document\.getElementById\(['"]([^'"]+)['"]\)/g;
while ((match = getElementByIdRegex.exec(js)) !== null) {
    if (!ids.has(match[1])) {
        console.log("Missing ID in HTML:", match[1]);
    }
}
