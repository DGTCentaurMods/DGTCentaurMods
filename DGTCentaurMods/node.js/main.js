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
    console.log('A user is connected.')

    socket.on('disconnect', () => {
        console.log('A user is disconnected.')
    })

    socket.on('request', (request) => {
        io.emit('request', request)
    })

    socket.on('web_message', (message) => {
        io.emit('web_message', message)
    })
})

server.listen(port, () => {
    console.log('listening on *:'+port)
})