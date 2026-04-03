const express = require('express');
const http = require('http');
const { Server } = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

// Health check route
app.get('/', (req, res) => {
    res.send('<h1>🚀 Multi-Militia Server is ONLINE!</h1><p>The socket.io server is ready to handle room connections.</p>');
});

/**
 * Rooms state: { passcode: Map(socketId -> playerData) }
 */
const rooms = {};

io.on('connection', (socket) => {
    console.log('--- User Connected:', socket.id);

    // Create Room
    socket.on('create_room', (data) => {
        const passcode = Math.random().toString(36).substring(2, 6).toUpperCase();
        rooms[passcode] = { players: new Map() };
        socket.join(passcode);
        socket.emit('room_created', { passcode, id: socket.id });
        console.log(`[CREATED] Room: ${passcode} by ${socket.id}`);
    });

    // Join Room
    socket.on('join_room', (passcode) => {
        passcode = passcode.toUpperCase();
        if (rooms[passcode]) {
            socket.join(passcode);
            socket.emit('room_joined', { passcode, id: socket.id });
            // Notify others
            socket.to(passcode).emit('player_joined', { id: socket.id });
            console.log(`[JOINED] User ${socket.id} joined Room: ${passcode}`);
        } else {
            socket.emit('error_msg', 'Room not found! Check passcode.');
        }
    });

    // Real-time synchronization
    socket.on('sync_pos', (data) => {
        // Find room
        const room = Array.from(socket.rooms).find(r => r !== socket.id);
        if (room && rooms[room]) {
            // Relays position and state to all other players in the room
            socket.to(room).emit('player_moved', { id: socket.id, ...data });
        }
    });

    // Combat events
    socket.on('shoot', (data) => {
        const room = Array.from(socket.rooms).find(r => r !== socket.id);
        if (room) socket.to(room).emit('player_shot', { id: socket.id, ...data });
    });

    socket.on('hit', (data) => {
        const room = Array.from(socket.rooms).find(r => r !== socket.id);
        if (room) socket.to(room).emit('player_hit', { id: socket.id, ...data });
    });

    socket.on('disconnecting', () => {
        const socketRooms = Array.from(socket.rooms);
        socketRooms.forEach(room => {
            if (rooms[room]) {
                socket.to(room).emit('player_left', { id: socket.id });
            }
        });
    });

    socket.on('disconnect', () => {
        console.log('--- User Disconnected:', socket.id);
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`
    =========================================
    MULTI-Militia Server Running!
    Port: ${PORT}
    Local Network: http://localhost:${PORT}
    =========================================
    `);
});
