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
			title:'',
		}

		me.menuitems = [{
				label:"Links", items: [
					{ label: "Open Lichess position analysis", action:() => me.onLichess() },
					{ label: "Go to legacy DGTCentaurMods site", action:() => me.onLegacy() },

				]
			}, { 
				label:"sample 2", items: [
					{ label: "submenu 1" },
					{ label: "submenu 2" },
					{ label: "submenu 3" },
					{ label: "submenu 4" },
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
					Chessboard.drawGraphicArrow(me.chessboard, message.uci_undo_move, { color:'orange' })
				}

				if (message.uci_move) {
					Chessboard.drawGraphicArrow(me.chessboard, message.uci_move, { color:"black" })
				}

				if (message.computer_uci_move) {
					Chessboard.drawGraphicArrow(me.chessboard, message.computer_uci_move, { color:"yellow" })
				}

				if (message.tip_uci_move) {
					Chessboard.drawGraphicArrow(me.chessboard, message.tip_uci_move, { color:"green" })
				}

				if (message.turn) {
					me.board.title = "turn → "+message.turn
				}

				if (message.title) {
					me.board.title = message.title
				}

				$scope.$apply()

				//me.socket.emit('ack', {result: true, text:"FEN has been properly updated!"});
			});

			// We ask the app to send us the current PGN and FEN
			me.socket.emit('request', {'fen':true, 'pgn': true, 'uci_move': true})

		}, 500)
	}
])