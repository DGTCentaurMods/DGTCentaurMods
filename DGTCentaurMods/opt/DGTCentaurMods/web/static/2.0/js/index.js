"use strict"

angular.module("dgt-centaur-mods", ['ngMaterial', 'angular-storage', 'ngAnimate'])

// Only there because of Flask conflict
.config(['$interpolateProvider', function($interpolateProvider) {
	$interpolateProvider.startSymbol('[[');
	$interpolateProvider.endSymbol(']]');
}])

.directive('board', function() {
	return {
		restrict: 'E',
		scope: {
			item: '=',
			main: '=',
			onLichess: '&',
			onPlay: '&',
			onUndo: '&',
			onPgn: '&',
			onFen: '&',
			onAnalyze: '&',
		},
		templateUrl: 'board.html'
	};
})

// Main page controller
.controller("MainController", ['$scope', '$rootScope', 'store','$timeout', '$mdDialog',
	function ($scope, $rootScope, $store, $timeout, $mdDialog) {
		const me = this

		const DEFAULT_POSITION = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

		const stockfish = new Worker('static/stockfish/stockfish.js')

		stockfish._lasteval = 0
		
		// FEN history (built from PGN)
		const history = {
			fens:[],
			index:0
		}

		// Board data
		me.board = {
			index:1,
			turn_caption:'-',
			turn:1,
			eval:50,
		}

		// Each display menu item is connected to a boolean main.board property
		const displaySettings = [
			{ id:"previous_move", default:true,  label: "Previous move", type:"checkbox"},
			{ id:"kings_checks", default:false,  label: "Kings checks", type:"checkbox"},
			{ id:"live_evaluation", default:true, label: "Live evaluation", type:"checkbox"},
		]

		// We read the cookies data and stores the values within me.board
		displaySettings.forEach((item) => me.board[item.id] = $store.get(item.id) == null ? item.default : $store.get(item.id))

		// Menu items
		me.menuitems = [{
				label:"Links", items: [
					{ label: "Open Lichess position analysis", action:() => me.onLichess() },
					{ label: "Go to legacy DGTCentaurMods site", action:() => me.onLegacy() },
				]
			}, { 
				label:"Display settings", items: displaySettings 
			}, { 
				label:"Previous games", items: [
					{ label: "Not available yet!", action:() => null },
				] 
			}, {
				label:"System", items: [
					{ label: "Power off board", action:() => {
							me.socket.emit('request', {'sys_action':'shutdown'})
							popupMessage('A shutdown request has been sent to the board!')

						} 
					},
					{ label: "Reboot board", action:() => {
							me.socket.emit('request', {'sys_action':'reboot'})
							popupMessage('A reboot request has been sent to the board!') 
						}
					},
					{ label: "Restart service", action:() => {
							me.socket.emit('request', {'sys_action':'restart_service'})
							popupMessage('A service restart request has been sent to the board!') 
						}
					},
					{ type: "divider"},
					{ label: "Last log events", action:() => {
						me.socket.emit('request', {'sys_action':'log_events'})
					}
				},
				]
			}
		]

		// Lichess analysis page
		me.onLichess = () => {
			window.open("https://lichess.org/analysis/ "+encodeURI(me.current_fen), "_blank")
			return
		}

		// Legacy web site
		me.onLegacy = () => {
			window.location = "/legacy"
			return
		}

		// Main menus function
		me.openMenu = function($menu, ev) {
			$menu.open(ev);
		};

		// Sub menus function
		me.executeMenu = function(item, ev) {
			if (item.action) item.action()
		};

		// Checkbox menus function
		me.executeCheckboxMenu = function(item, ev) {
			if (item.id) {
				// We reverse the value then store it
				me.board[item.id] = !me.board[item.id]
				$store.set(item.id, me.board[item.id])
			}
		};

		// Chessboard builder
		// If needed, we could display several boards in the same page...
		var buildChessboard = (q, options = {}) => {

			let board = Chessboard('board'+q.index, {

				showNotation: true,
				orientation: 'white',
				draggable: false,

				pieceTheme:'static/2.0/images/pieces/{piece}.png',
			})

			if (options.keyboard) {
				document.onkeydown = function (e) {
					switch (e.code) {
						case "ArrowRight":
							if (history.index<history.fens.length-1)
								history.index++
								me.chessboard.position(history.fens[history.index])

							e.preventDefault()
							break;
						case "ArrowLeft":
							if (history.index>0)
								history.index--
								me.chessboard.position(history.fens[history.index])

							e.preventDefault()
							break;
						default:
							break;
					}
				}
			}

			// Arrows canvas
			q.overlay = new ChessboardArrows(q)

			board.id = q.index

			return board
		}

		// Stockfish evaluation feedback
		stockfish.onmessage = (event) => {

			if (event.data) {

				//console.log(event.data)

				// Stockfish evaluation finishes with the bestmove message
				if (event.data.includes("bestmove")) {
					me.board.eval = 50+stockfish._lasteval
					$scope.$apply()
				}
				
				// Stockfish evaluation feedback
				if (event.data.includes("score cp")) {

					// info depth 1 seldepth 1 multipv 1 score cp -537 nodes
					const regexp = /score\ cp\ ([^ ]+)\ /gi
					const matches = regexp.exec(event.data)

					const MAX_VALUE = 600

					if (matches && matches.length) {

						let value = parseInt(matches[1])

						// black plays?
						if (me.board.turn == 0) value = -value
			
						if (value >  MAX_VALUE) value =  MAX_VALUE
						if (value < -MAX_VALUE) value = -MAX_VALUE

						value = parseInt((value/(MAX_VALUE *2)) * 100)

						stockfish._lasteval = value
					}
				}

				// Stockfish detected (future) mat state
				if (event.data.includes("score mate")) {

					let value = 50

					// black plays?
					if (me.board.turn == 0) value = -value

					stockfish._lasteval = value

					me.board.eval = 50+value
					$scope.$apply()
				}
			}
		}

		 var popupMessage = (message) => {
			$mdDialog.show(
				$mdDialog.alert()
				  .clickOutsideToClose(true)
				  .title('♔ '+document.title+' ♔')
				  .textContent(message)
				  .ariaLabel(message)
				  .ok('Got it!'))
		 }

		$timeout(() => {

			me.chessboard = buildChessboard(me.board, { keyboard:true })

			me.socket = io()

			me.socket.on("error", (error) => {
				console.log(error)
			})

			me.socket.on("connect", () => {
				console.log("Connected to the server.")
			})

			me.socket.on("disconnect", (reason) => {
				console.log("Disonnected to the server.")
				if (reason === "io server disconnect") {
				  // The disconnection was initiated by the server, you need to reconnect manually
				  me.socket.connect()
				}
				// Else the socket will automatically try to reconnect
			})

			// We receive data from the server app
			me.socket.on('message', function(message) {
				//console.log(message)

				// Shortcuts to make the code more readable...
				const arrow = Chessboard.drawGraphicArrow
				const square = Chessboard.drawGraphicSquare

				const socketmessages = {

					// We receive last log events
					log_data: (value) => {
						me.logData = value.join('\n')
						$mdDialog.show({
							contentElement: '#log_data',
							parent: angular.element(document.body),
							targetEvent: null,
							clickOutsideToClose: true
						})
					},

					// We clear the graphics (not the user ones)
					clear_board_graphic_moves: () => Chessboard.clearGraphicArrow(me.chessboard),
					
					// We receive a new postion
					fen: (value) => {

						if (me.current_fen != value) {
	
							// We determinate from the FEN which color plays
							me.board.turn = value.includes(' w ') ? 1 : 0
	
							me.board.turn_caption = "turn → "+(me.board.turn ? 'white' : 'black')
	
							me.chessboard.position(value)
							me.current_fen = value
	
							// We trigger the evaluation on new FEN only
							if (me.board.live_evaluation) {
								stockfish.postMessage("position fen " + value)
								stockfish.postMessage("go depth 12")
							}
						}
					},

					// We receive the current PGN, formatted by the server
					pgn: (value) => {
						me.current_pgn = value

						let moves = (() => {
							const c = new Chess()
							c.load_pgn(value)
							return c.history()
						})()

						// We build the FEN history
						history.fens = [DEFAULT_POSITION]

						var c = new Chess()

						moves.forEach(m => {
							c.move(m)
							history.fens.push(c.fen())
						})

						history.index = history.fens.length-1
					},

					// Last move has been taken back - we draw it
					uci_undo_move: (value) => {
						arrow(me.chessboard, value.slice(0, 2), { color:'orange' })
						arrow(me.chessboard, value, { color:'orange' })
					},

					// We draw the previous move
					uci_move: (value) => {
					
						if (me.board.previous_move) {
							square(me.chessboard, value.slice(0, 2), { color:"black" })
							arrow(me.chessboard, value, { color:"black" })
						}
					},

					// We draw the computer move
					computer_uci_move: (value) => arrow(me.chessboard, value, { color:"yellow" }),

					// We draw the hint
					tip_uci_move: (value) => arrow(me.chessboard, value, { color:"green" }),
				
					// We draw the checks
					checkers: (value) => {
						if (me.board.kings_checks && value.length>0 && message.kings) {
					
							let kingSquare = message.kings[1 -me.board.turn]
							square(me.chessboard, kingSquare, { color:"red" })
							
							value.forEach(item => {	
								arrow(me.chessboard, item+kingSquare, { color:"red" })
							})
						}
					},

					// We override the default turn caption
					turn_caption: (value) => {
						me.board.turn_caption = value
					}
				}

				for(var id in socketmessages) {
					// Does the message contain the id?
					// If yes we call the function
					if (message[id]) socketmessages[id](message[id])
				}

				$scope.$apply()
			});

			// We ask the app to send us the current PGN, FEN and previous move
			me.socket.emit('request', {'fen':true, 'pgn': true, 'uci_move': true})

			popupMessage('Welcome!This web interface is being tested!\nYou can come back to the legacy interface anytime using the menu.')

		}, 500)
	}
])