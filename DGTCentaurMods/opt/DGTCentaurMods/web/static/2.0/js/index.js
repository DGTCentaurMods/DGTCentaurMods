"use strict"

angular.module("dgt-centaur-mods", ['ngMaterial', 'angular-storage', 'ngAnimate', 'dgt-centaur-mods.lib'])

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

.filter('html', function($sce) {
	return function(value) {
		//value = (value || '').replace('@@', '#')
		return $sce.trustAsHtml(value)
	}
})

// Main page controller
.controller("MainController", ['$scope', '$rootScope', 'store','$timeout', '$mdDialog', '$history',
	function ($scope, $rootScope, $store, $timeout, $mdDialog, $history) {
		const me = this

		const stockfish = new Worker('static/stockfish/stockfish.js')

		stockfish._lasteval = 0
		
		me.currentGame = { id: -1 }

		// Board data
		me.board = {
			index:1,
			turn_caption:'-',
			turn:1,
			eval:50,
			synchronized:true,

			history: $history
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
					{ label: "Open Lichess position analysis", action:() => window.open("https://lichess.org/analysis/ "+encodeURI(me.current_fen), "_blank") },
					{ label: "Open Lichess PGN import page", action:() => window.open("https://lichess.org/paste", "_blank") },
					//{ label: "Go to legacy DGTCentaurMods site", action:() => me.onLegacy() },
				]
			}, { 
				label:"Display settings", items: displaySettings 
			}, { 
				label:"Previous games", items: [], action:() => {
					SOCKET.emit('request', {'data':'previous_games'})
				} 
			}, {
				label:"System", items: [
					{ label: "Power off board", action:() => {
							SOCKET.emit('request', {'sys_action':'shutdown'})
							popupMessage('A shutdown request has been sent to the board!')

						} 
					},
					{ label: "Reboot board", action:() => {
							SOCKET.emit('request', {'sys_action':'reboot'})
							popupMessage('A reboot request has been sent to the board!') 
						}
					},
					{ label: "Restart service", action:() => {
							SOCKET.emit('request', {'sys_action':'restart_service'})
							popupMessage('A service restart request has been sent to the board!') 
						}
					},
					{ type: "divider"},
					{ label: "Last log events", action:() => {
							SOCKET.emit('request', {'sys_action':'log_events'})
						}
					},
				]
			}
		]

		// Main menus function
		me.openMenu = function($menu, menu, ev) {
			if (menu.action) {
				menu.action()
			} else
				$menu.open(ev)
		}

		// Sub menus function
		me.executeMenu = function(item, ev) {
			if (item.action) item.action()
		}

		// Checkbox menus function
		me.executeCheckboxMenu = function(item, ev) {
			if (item.id) {
				// We reverse the value then store it
				me.board[item.id] = !me.board[item.id]
				$store.set(item.id, me.board[item.id])
			}
		}

		me.onGameLoad = function(game, iscurrent) {
			if (iscurrent) {
				// We ask the app to send us the current PGN, FEN and previous move
				SOCKET.emit('request', {'fen':true, 'pgn': true, 'uci_move': true})
			}
			else {
				SOCKET.emit('request', {'data':'game_moves', 'id':game.id})
				me.currentGame = game
				me.board.synchronized = false
			}
			$mdDialog.cancel()
		}

		me.onGameRemove = function(game) {
			SOCKET.emit('request', {'data':'remove_game', 'id':game.id})
			$mdDialog.cancel()
		}

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
							me.board.history.forward(me.chessboard)
							$scope.$apply()
							e.preventDefault()
							break;
						case "ArrowLeft":
							me.board.history.backward(me.chessboard)
							$scope.$apply()
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

					const MAX_VALUE = 1500

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

		const popupMessage = (message) => {
			$mdDialog.show(
				$mdDialog.alert()
				  .clickOutsideToClose(true)
				  .title('♔ '+document.title+' ♔')
				  .textContent(message)
				  .ariaLabel(message)
				  .ok('Got it!'))
		 }

		const createUUID = () => {
			var dt = new Date().getTime()
			var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
				var r = (dt + Math.random()*16)%16 | 0
				dt = Math.floor(dt/16)
				return (c=='x' ? r :(r&0x3|0x8)).toString(16)
			})
			return uuid
		}

		const socketBuilder = () => {

			var _instance = null
			var _uuid = createUUID()

			var _emit = (id, message) => {
				if (_instance != null) {
					message.uuid = _uuid
					_instance.emit(id, message)
				}
			}

			return {

				initialize: () => {
					if (_instance == null) {
						_instance = io()

						_instance .on("error", (error) => {
							console.log(error)
						})
			
						_instance .on("connect", () => {
							console.log("Connected to the server.")

							// We ask the app to send us the current PGN, FEN and previous move
							_emit('request', {'fen':true, 'pgn': true, 'uci_move': true})
							
						})
			
						_instance.on("disconnect", (reason) => {
							console.log("Disonnected to the server.")
							if (reason === "io server disconnect") {
								// The disconnection was initiated by the server, you need to reconnect manually
								_instance.connect()
							}
							// Else the socket will automatically try to reconnect
						})
			
						// We receive data from the server app
						_instance.on('message', function(message) {
							//console.log(message)

							// Message might be not for us...
							if (message.uuid && message.uuid != _uuid) return
			
							// Shortcuts to make the code more readable...
							const arrow = Chessboard.drawGraphicArrow
							const square = Chessboard.drawGraphicSquare
			
							const socketmessages = {

								popup: (value) => {
									popupMessage(value)
								},

								// Previous games have been resquested
								previous_games: (value) => {

									me.games = value
									$mdDialog.show({
										contentElement: '#previous_games',
										parent: angular.element(document.body),
										targetEvent: null,
										clickOutsideToClose: true
									})

								},

								// Game moves have been resquested
								game_moves: (uciMoves) => {

									me.board.history.initFromMoves(uciMoves)
									me.board.history.go(me.chessboard, 0)

									Chessboard.clearGraphicArrow(me.chessboard)
								},
			
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
								
								// We receive a new position
								fen: (value) => {
			
									if (me.current_fen != value || me.board.synchronized == false) {

										me.board.synchronized = true
				
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
								pgn: (pgn) => {

									me.board.history.initFromPGN(pgn)
									me.board.history.go(me.chessboard, -1)
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
						})
					}
					return _instance
				},

				emit: (id, message) => _emit(id, message)
			}
		}

		const SOCKET = socketBuilder()

		$timeout(() => {

			me.chessboard = buildChessboard(me.board, { keyboard:true })

			SOCKET.initialize()
			
		}, 500)
	}
])