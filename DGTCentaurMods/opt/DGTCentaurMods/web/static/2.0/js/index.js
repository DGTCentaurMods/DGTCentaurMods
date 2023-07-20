"use strict"

angular.module("dgt-centaur-mods", ['ngMaterial', 'ngAnimate'])

// Only there because of Flask conflict
.config(['$interpolateProvider', function($interpolateProvider) {
	$interpolateProvider.startSymbol('[[');
	$interpolateProvider.endSymbol(']]');
}])

// Main page controller
.controller("MainController", ['$scope','$rootScope', '$timeout', '$mdDialog',
	function ($scope, $rootScope, $timeout, $mdDialog) {
		var me = this

		var buildChessboard = (index, options = {}) => {

			let board = Chessboard('board'+index, {

				showNotation: true,
				orientation: 'white',
				draggable: false,

				pieceTheme:'static/2.0/images/pieces/{piece}.png',
			})

			board.id = 'board'+index

			return board
		}

		me.chessboard = buildChessboard(1)

		me.socket = io();

		// We receive data from the server app
		me.socket.on('message', function(message) {
			//console.log(message)

			if (message.fen) {
				me.chessboard.position(message.fen)
				me.current_fen = message.fen
			}
			if (message.pgn) me.current_pgn = message.pgn

			$scope.$apply()

			//me.socket.emit('ack', {result: true, text:"FEN has been properly updated!"});
		});

		// We ask the app to send us the current PGN and FEN
    	me.socket.emit('request', {'fen':true, 'pgn': true})
	}
])