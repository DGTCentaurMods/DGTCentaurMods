"use strict"

angular.module("dgt-centaur-mods", ['ngMaterial'])

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
.controller("MainController", ['$scope','$rootScope', '$timeout', '$mdMenu', '$mdDialog',
	function ($scope, $rootScope, $timeout, $mdMenu, $mdDialog) {
		var me = this

		me.board = {
			index:1,
			turn_caption:'',

			previous_move:true,
			kings_checks:true,
		}

		me.foobar = true

		me.menuitems = [{
				label:"Links", items: [
					{ label: "Open Lichess position analysis", action:() => me.onLichess() },
					{ label: "Go to legacy DGTCentaurMods site", action:() => me.onLegacy() },
				]
			}, { 
				label:"Display settings", items: [
					{ id:"previous_move", label: "display previous move", type:"checkbox"},
					{ id:"kings_checks", label: "display kings checks", type:"checkbox"}
				]
			},
		]

		me.onLichess = () => {
			window.open("https://lichess.org/analysis/ "+encodeURI(me.current_fen), "_blank")
			return
		}

		me.onLegacy = () => {
			window.location = "/legacy"
			return
		}

		me.openMenu = function($menu, ev) {
			$menu.open(ev);
		};

		me.executeMenu = function(item, ev) {
			if (item.action) item.action()
		};

		me.executeCheckboxMenu = function(item, ev) {
			if (item.id) {
				if (typeof me.board[item.id] !== "boolean") {
					me.board[item.id] = true
				} else {
					me.board[item.id] = !me.board[item.id]
				}
			}
		};

		var buildChessboard = (q, options = {}) => {

			let board = Chessboard('board'+q.index, {

				showNotation: true,
				orientation: 'white',
				draggable: false,

				pieceTheme:'static/2.0/images/pieces/{piece}.png',
			})

			if (options.keyboard) {
				document.getElementById('board_wrapper'+q.index).onkeydown = function (e) {
					switch (e.code) {
						case "ArrowRight":
							//$scope.$apply(()=>me.onHistory(q, 1))
							e.preventDefault()
							break;
						case "ArrowLeft":
							//$scope.$apply(()=>me.onHistory(q, -1))
							e.preventDefault()
							break;
						case "ArrowUp":
							//$scope.$apply(()=>me.onHistory(q, 999))
							e.preventDefault()
							break;
						case "ArrowDown":
							//$scope.$apply(()=>me.onHistory(q, -999))
							e.preventDefault()
							break;
						default:
							break;
					}
				}
			}

			q.chessboard = board
			q.overlay = new ChessboardArrows(q)

			board.id = q.index

			return board
		}

		$timeout(() => {

			me.chessboard = buildChessboard(me.board)

			me.socket = io();

			// We receive data from the server app
			me.socket.on('message', function(message) {
				//console.log(message)

				if (message.clear_board_graphic_moves) {
					Chessboard.clearGraphicArrow(me.chessboard)
				}
				
				if (message.fen) {
					me.chessboard.position(message.fen)
					me.current_fen = message.fen
				}
				
				if (message.pgn) me.current_pgn = message.pgn

				if (message.uci_undo_move) {
					Chessboard.drawGraphicArrow(me.chessboard, message.uci_undo_move.slice(0, 2), { color:'orange' })
					Chessboard.drawGraphicArrow(me.chessboard, message.uci_undo_move, { color:'orange' })
				}

				if (me.board.previous_move && message.uci_move) {
					Chessboard.drawGraphicSquare(me.chessboard, message.uci_move.slice(0, 2), { color:"black" })
					Chessboard.drawGraphicArrow(me.chessboard, message.uci_move, { color:"black" })
				}

				if (message.computer_uci_move) {
					Chessboard.drawGraphicArrow(me.chessboard, message.computer_uci_move, { color:"yellow" })
				}

				if (message.tip_uci_move) {
					Chessboard.drawGraphicArrow(me.chessboard, message.tip_uci_move, { color:"green" })
				}

				// checks
				if (me.board.kings_checks && message.checkers && message.checkers.length>0 && message.kings && message.turn) {
					
					let kingSquare = message.kings[message.turn == "white"?0:1]
					Chessboard.drawGraphicSquare(me.chessboard, kingSquare, { color:"red" })
					
					message.checkers.forEach(item => {	
						Chessboard.drawGraphicArrow(me.chessboard, item+kingSquare, { color:"red" })
					})
				}

				if (message.turn) {
					me.board.turn_caption = "turn → "+message.turn
				}

				if (message.turn_caption) {
					me.board.turn_caption = message.turn_caption
				}

				$scope.$apply()

				//me.socket.emit('ack', {result: true, text:"FEN has been properly updated!"});
			});

			// We ask the app to send us the current PGN and FEN
			me.socket.emit('request', {'fen':true, 'pgn': true, 'uci_move': true})

		}, 500)
	}
])