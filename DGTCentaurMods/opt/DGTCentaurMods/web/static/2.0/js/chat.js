// This file is part of the DGTCentaur Mods open source software
// ( https://github.com/Alistair-Crompton/DGTCentaurMods )
//
// DGTCentaur Mods is free software: you can redistribute
// it and/or modify it under the terms of the GNU General Public
// License as published by the Free Software Foundation, either
// version 3 of the License, or (at your option) any later version.
//
// DGTCentaur Mods is distributed in the hope that it will
// be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
// of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this file.  If not, see
//
// https://github.com/Alistair-Crompton/DGTCentaurMods/blob/master/LICENSE.md
//
// This and any other notices must remain intact and unaltered in any
// distribution, modification, variant, or derivative of this software.

"use strict";

angular.module("dgt-centaur-mods.lib.chat", [])

    .factory('$chat', ['$timeout', function($timeout) {

        var _COLORS = ['black','red','blue','green','orange','darkmagenta','hotpink','brown','chocolate','darkblue','darkgreen']

        var _items = []
        var _onSubmit = () => true
        var _colors = {}

        return (() => {

            var current_colors = []

            return {
                message: "",

                initialize: (onSubmit) => {
                    _onSubmit = onSubmit
                },

                items: () => _items,

                submit: (me) => {
                    _onSubmit(me.message.trim())
                    me.message=""
                },

                add: (value) => {

                    if (!value.cuuid) return

                    if (current_colors.length == 0) current_colors = [..._COLORS]

                    value.color = _colors[value.cuuid] || current_colors.pop() 
                    _colors[value.cuuid] = value.color

                    value.ts = new Date().toLocaleTimeString()
                    
                    if (_items.length>13) _items.shift()
                    
                    _items.push(value)
                }
            }
        })()
    }])