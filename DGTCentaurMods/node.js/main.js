const express = require('express')
const app = express()
const http = require('http')
const server = http.createServer(app)
const { Server } = require("socket.io")
const io = new Server(server)

const port = process.env.PORT || 3000
const connectionString = process.env.PGSTRING

console.log(process.argv)

console.log("PORT (ENV):"+process.env.PORT)
console.log("PORT:"+port)
console.log("PG_CSTRING:"+connectionString)

const { Pool, Client } = require('pg')

const pool = new Pool({ connectionString })

//app.get('/', (req, res) => {
//    res.send('<h2>Alistair-Centaur-Mods socket.io server</h2>')
//})

async function main(){

    const client = new Client({ connectionString })
 
    try {

        const result = await pool.query('SELECT NOW()')
        console.log(result.rows[0])

        //await client.connect()
        //console.log('Database Connected.')

    } catch (e) {
        console.error(e)
    } finally {
        //await client.end()
        console.log('Done.')
    }
}
 
main().catch(console.error)

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