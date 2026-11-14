const express = require('express');
const fs = require('fs');
const app = express();

// SEC-001: Hardcoded secret
const api_key = "api_key=abcdef12345678901234";

// JS-001: Synchronous blocking file read on server startup/request
const configData = fs.readFileSync('/tmp/config.json', 'utf-8');

// EXPRESS-003: Async route handler without try/catch or async wrapper
app.get('/unhandled-async', async (req, res) => {
    // JS-003: Dangerous eval
    const computed = eval(req.query.code);
    res.json({ result: computed });
});

// Notice: No 4-parameter error middleware registered (EXPRESS-001)
// Notice: No /health or /healthz endpoint (PROD-001)

module.exports = app;
