const express = require('express');
const app = express();

app.use(express.json());

// Health endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok' });
});

// Proper async route with try/catch
app.get('/api/data', async (req, res, next) => {
    try {
        const data = { message: 'hello' };
        res.json(data);
    } catch (err) {
        next(err);
    }
});

// Centralized 4-argument error handling middleware
app.use((err, req, res, next) => {
    res.status(500).json({ error: 'Internal Server Error' });
});

module.exports = app;
