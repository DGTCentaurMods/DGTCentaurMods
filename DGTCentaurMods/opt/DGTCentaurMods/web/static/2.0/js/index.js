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
		
		const history = {
			fens:[],
			index:0
		}

		stockfish._lasteval = 0

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

		// Board data
		me.board = {
			index:1,
			turn_caption:'-',
			turn:1,
			eval:50,
		}

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
					{ label: "Power off board", action:() => me.socket.emit('request', {'sys_action':'shutdown'}) },
					{ label: "Reboot board", action:() => me.socket.emit('request', {'sys_action':'reboot'}) },
					{ label: "Restart service", action:() => me.socket.emit('request', {'sys_action':'restart_service'}) },
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

		$timeout(() => {

			me.chessboard = buildChessboard(me.board, { keyboard:true })

			me.socket = io();

			// We receive data from the server app
			me.socket.on('message', function(message) {
				//console.log(message)

				if (message.clear_board_graphic_moves) {
					Chessboard.clearGraphicArrow(me.chessboard)
				}
				
				if (message.fen) {

					if (me.current_fen != message.fen) {

						// We determinate from the FEN which color plays
						me.board.turn = message.fen.includes(' w ') ? 1 : 0

						me.board.turn_caption = "turn → "+(me.board.turn ? 'white' : 'black')

						me.chessboard.position(message.fen)
						me.current_fen = message.fen

						// We trigger the evaluation on new FEN only
						if (me.board.live_evaluation) {
							stockfish.postMessage("position fen " + message.fen)
							stockfish.postMessage("go depth 12")
						}
					}
				}
				
				// The PGN has been formatted by the server
				if (message.pgn) {
					me.current_pgn = message.pgn

					let moves = (() => {
						const c = new Chess()
						c.load_pgn(message.pgn)
						return c.history()
					})()

					history.fens = [DEFAULT_POSITION]

					var c = new Chess()

					moves.forEach(m => {
						c.move(m)
						history.fens.push(c.fen())
					})

					history.index = history.fens.length-1
				}

				// Shortcuts to make the code more readable...
				const arrow = Chessboard.drawGraphicArrow
				const square = Chessboard.drawGraphicSquare

				// Last move has been taken back - we draw it
				if (message.uci_undo_move) {
					arrow(me.chessboard, message.uci_undo_move.slice(0, 2), { color:'orange' })
					arrow(me.chessboard, message.uci_undo_move, { color:'orange' })
				}

				// We draw the previous move
				if (me.board.previous_move && message.uci_move) {
					square(me.chessboard, message.uci_move.slice(0, 2), { color:"black" })
					arrow(me.chessboard, message.uci_move, { color:"black" })
				}

				// We draw the computer move
				if (message.computer_uci_move) {
					arrow(me.chessboard, message.computer_uci_move, { color:"yellow" })
				}

				// We draw the hint
				if (message.tip_uci_move) {
					arrow(me.chessboard, message.tip_uci_move, { color:"green" })
				}

				// We draw the checks
				if (me.board.kings_checks && message.checkers && message.checkers.length>0 && message.kings) {
					
					let kingSquare = message.kings[1 -me.board.turn]
					square(me.chessboard, kingSquare, { color:"red" })
					
					message.checkers.forEach(item => {	
						arrow(me.chessboard, item+kingSquare, { color:"red" })
					})
				}

				// We override the default turn caption
				if (message.turn_caption) {
					me.board.turn_caption = message.turn_caption
				}

				$scope.$apply()
			});

			// We ask the app to send us the current PGN, FEN and previous move
			me.socket.emit('request', {'fen':true, 'pgn': true, 'uci_move': true})

		}, 500)
	}
])