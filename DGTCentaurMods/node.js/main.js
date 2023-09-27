const express = require('express')
const app = express()
const http = require('http')
const server = http.createServer(app)
const { Server } = require("socket.io")
const io = new Server(server)

const port = process.env.PORT || 3000

app.get('/', (req, res) => {
    res.send('<h2>Alistair-Centaur-Mods socket.io server</h2>')
})

io.on('connection', (socket) => {
    console.log('a user connected')
    socket.on('disconnect', () => {
        console.log('user disconnected')
    })

    socket.on('message', (message) => {
        io.emit('message', message)
    })
})

server.listen(port, () => {
    console.log('listening on *:'+port)
})