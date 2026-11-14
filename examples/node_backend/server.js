const express = require('express');
const app = express();

app.use(express.json());

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

app.get('/items', async (req, res, next) => {
    try {
        const items = [{ id: '1', name: 'Item 1' }];
        res.json(items);
    } catch (err) {
        next(err);
    }
});

// Centralized error middleware
app.use((err, req, res, next) => {
    res.status(500).json({ error: 'Internal Server Error' });
});

app.listen(3000, () => {
    console.info('Server running on port 3000');
});

