"use strict";

angular.module("dgt-centaur-mods.lib", [])

	.factory('$history', ['$timeout', function($timeout) {

		const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

		return (() => {
            
            var _fens = []
            var _index = 0
            var _pgnlist = []
            var _pgn = ""

            var _update_pgnlist = () => {
                const rows = _pgn.split('\n')

                _pgnlist = []

                rows.forEach((row, i) => {
                    let items = row.split(' ')

                    let move = { index:(i*2)+1, wsan:items[1], bsan:'' }
                    if (items[2]) move.bsan = items[2]
                    _pgnlist.push(move)
                })
            }

            return {

                index: () => _index,
                pgnlist: () => _pgnlist,
                pgn: () => _pgn,

                initFromPGN: (value) => {

                    _pgn = value

                    // We get all the history
                    let moves = (() => {
                        const c = new Chess()
                        c.load_pgn(_pgn)
                        return c.history()
                    })()

                    // We build the FEN history
                    _fens = [START_FEN]

                    var c = new Chess()

                    moves.forEach(m => {
                        c.move(m)
                        _fens.push(c.fen())
                    })

                    _update_pgnlist()
                },

                initFromMoves: (uciMoves) => {
                    // We build the FEN history
                    _fens = [START_FEN]

                    let c = new Chess()

                    _pgn = ""
                    
                    let moveIndex = 0

                    uciMoves.forEach(m => {
                        if (m) {
                            const move = c.move(m, { sloppy:true })
                            if (move.color == 'w') {
                                ++moveIndex
                                _pgn = _pgn + moveIndex + '. ' + move.san
                            }
                            else {
                                _pgn = _pgn + ' ' + move.san + '\n'
                            }
                            _fens.push(c.fen())
                        }
                    })

                    _update_pgnlist()
                },

                forward: (chessboard) => {
                    if (_index<_fens.length-1) {
                        _index++
                        chessboard.position(_fens[_index])
                    }
                },

                backward: (chessboard) => {
                    if (_index>0) {
                        _index--
                        chessboard.position(_fens[_index])
                    }
                },

                go: (chessboard, value) => {
                    _index = value == -1?_fens.length-1:value
                    chessboard.position(_fens[_index])
                }
            }
        })()
	}])