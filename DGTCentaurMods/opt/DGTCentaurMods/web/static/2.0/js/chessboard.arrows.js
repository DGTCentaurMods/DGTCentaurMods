"use strict"

var isTouchDevice = () => 'ontouchstart' in document.documentElement

Chessboard.parseCol = (c) => {
	return {a:1,b:2,c:3,d:4,e:5,f:6,g:7,h:8}[c] 
}

Chessboard.toSquare = (row, col) => {
	return 'abcdefgh'[col-1]+(9-row)
}

Chessboard.drawGraphicArrowFromComment = (q) => {

	let c = _.find(q.comments, (c) => c.fen == q.chessboard.game.fen())

	Chessboard.clearGraphicArrow(q.chessboard, {canvas:"fx3"})

	if (!c) return

	q.chessboard.fx3 = true

	q.comment = c.comment

	let csls = /\[\%csl\s+([^\]]+)\]/g.exec(q.comment)
	if (csls) {
		q.comment = q.comment.replace(csls[0], '')
		csls = csls && csls[1] ? csls[1].split(',') : []
	}

	_.each(csls, (csl) => {
		csl = csl.trim()

		Chessboard.drawGraphicSquare(q.chessboard, csl[1]+csl[2], {
			
			canvas:"fx3",

			color:{
				G:"green",
				Y:"yellow",
				R:"red",
				W:"white",
				B:"DeepSkyBlue",
				P:"Purple",
				K:"black",
				O:"orange" }[csl[0]],
			
				duration:"infinite"})
	})

	//%cal Gc2c3,Rc3d4
	let cals = /\[\%cal\s+([^\]]+)\]/g.exec(q.comment)
	if (cals) {
		q.comment = q.comment.replace(cals[0], '')
		cals = cals && cals[1] ? cals[1].split(',') : []
	}
	
	_.each(cals, (cal) => {

		cal = cal.trim()

		Chessboard.drawGraphicArrow(q.chessboard, cal[1]+cal[2]+cal[3]+cal[4], {
			
			canvas:"fx3",

			color:{
				G:"green",
				Y:"yellow",
				R:"red",
				W:"white",
				B:"DeepSkyBlue",
				P:"Purple",
				K:"black",
				O:"orange" }[cal[0]], 
			
				duration:"infinite"})
	})

	q.chessboard.ui_comment = q.comment.replaceAll('<br/>', '\n')
}

Chessboard.drawGraphicArrow = (board, move, options = {}) => {

	let p = { iscal: options.iscal || false, cid:options.canvas || "moves_canvas", color:options.color || "yellow", duration:options.duration || 1000 }

	if (p.iscal) {

		// new way
		// [%csl Ra1,Ga2]
		// Rg1f3 Ra1 Ga2

		_.each(_.filter(move.split(" "), (m) => m.length == 3), (csl) => {

			Chessboard._drawSquare(
				p.cid+"_"+board.id, 
				csl[1]+csl[2],
				board.orientation() == 'black', 
				{
					G:"green",
					Y:"yellow",
					R:"red",
					W:"white",
					B:"DeepSkyBlue",
					P:"Purple",
					K:"black",
					O:"orange" }[csl[0]])
		})

		// new way
		// [%cal Rg1f3,Rf3e5,Rf4c7,Rc7b6]
		// Rg1f3 Rf3e5 Rf4c7 Rc7b6
		_.each(_.filter(move.split(" "), (m) => m.length == 5), (cal) => {

			Chessboard._drawArrow(
				p.cid+"_"+board.id, 
				cal[1]+cal[2]+cal[3]+cal[4],
				board.orientation() == 'black', 
				{
					G:"green",
					Y:"yellow",
					R:"red",
					W:"white",
					B:"DeepSkyBlue",
					P:"Purple",
					K:"black",
					O:"orange" }[cal[0]])
		})
		
	} else {
		// old way
		Chessboard._drawArrow(p.cid+"_"+board.id, move, board.orientation() == 'black', p.color)
	}
	
	board[p.cid] = true

	/*if (p.duration != "infinite") {
		window.setTimeout(() => 
			board.scope.$apply(() => {
				Chessboard.clearGraphicArrow(board, options)
			}), p.duration)
	}*/
}

Chessboard.drawGraphicSquare = (board, move, options) => {

	let p = { cid:options.canvas || "moves_canvas", color:options.color || "yellow", duration:options.duration || 1000 }
	
	Chessboard._drawSquare(p.cid+"_"+board.id, move, board.orientation() == 'black', p.color)
	board[p.cid] = true

	/*if (p.duration != "infinite") {
		window.setTimeout(() => 
			board.scope.$apply(() => {
				Chessboard.clearGraphicArrow(board, options)
			}), p.duration)
	}*/
}

Chessboard.clearGraphicArrow = (board, options={}) => {

	let cid = options.canvas || "moves_canvas"
	board[cid] = false
	let canvas = document.getElementById(cid+"_"+board.id)
	let ctx = canvas.getContext("2d")
	ctx.clearRect(0, 0, canvas.width, canvas.height)
}

Chessboard._drawSquare = (canvas_id, square, reversed, color) => {
	if (!square || square.length != 2) return

	var canvas = document.getElementById(canvas_id)
	var ctx = canvas.getContext("2d")

	let x0 = Chessboard.parseCol(square[0])
	let y0 = 9 -parseInt(square[1])

	if (reversed) {
		x0 = 9-x0
		y0 = 9-y0
	}

	const sqsize = (canvas.clientWidth-2) /8

	x0 = (x0*sqsize) - (sqsize*.5)
	y0 = (y0*sqsize) - (sqsize*.5)

	ctx.fillStyle = color
	ctx.strokeStyle = color

	ctx.beginPath();
	ctx.lineWidth = 10;
	ctx.rect(x0-(sqsize*.5)-1, y0-(sqsize*.5)-1, sqsize, sqsize)
	ctx.stroke()
}


Chessboard._drawArrow = (canvas_id, move, reversed, color) => {

	if (!move || move.length<4) return

	//variables to be used when creating the arrow
	var canvas = document.getElementById(canvas_id)
	var ctx = canvas.getContext("2d")
	ctx.lineCap = "round"

	//ctx.fillStyle = "rgba(255, 255, 255, 1)"
	//ctx.fillRect(0, 0, canvas.width, canvas.height)

	// ctx.fillStyle = "blue"
	// ctx.fillRect(0, 0, canvas.width, canvas.height)

	var _drawArrow = (x0, y0, x1, y1, width, head_len, singleline) => {

		const sqsize = (canvas.clientWidth-2) /8

		x0 = (x0*sqsize) - (sqsize*.5)
		y0= (y0*sqsize) - (sqsize*.5)
		x1 = (x1*sqsize) - (sqsize*.5)
		y1 = (y1*sqsize) - (sqsize*.5)

		// const width = 10
		// const head_len = 16
		const head_angle = Math.PI / 6
		const angle = Math.atan2(y1 - y0, x1 - x0)

		ctx.lineWidth = width
		ctx.fillStyle = color
		ctx.strokeStyle = color

		if (!singleline) {
			// adjust the point
			x1 -= width * Math.cos(angle)
			y1 -= width * Math.sin(angle)
		}	

		ctx.beginPath()
		ctx.moveTo(x0, y0)
		ctx.lineTo(x1, y1)
		ctx.stroke()

		if (singleline) return

		ctx.beginPath()
		ctx.lineTo(x1, y1)
		ctx.lineTo(x1 - head_len * Math.cos(angle - head_angle), y1 - head_len * Math.sin(angle - head_angle))
		ctx.lineTo(x1 - head_len * Math.cos(angle + head_angle), y1 - head_len * Math.sin(angle + head_angle))
		ctx.closePath()
		ctx.stroke()
		ctx.fill()
	}

	do {

		let sarrow = move.slice(0,4)
		move = move.slice(5)

		let singleline = sarrow[2]+sarrow[3] == move[0]+move[1]

		let x0 = Chessboard.parseCol(sarrow[0])
		let y0 = 9 -parseInt(sarrow[1])
		let x1 = Chessboard.parseCol(sarrow[2])
		let y1 = 9 -parseInt(sarrow[3])

		if (reversed) {
			x0 = 9-x0
			y0 = 9-y0
			x1 = 9-x1
			y1 = 9-y1
		}

		let shift_value = .2

		let _x0 = x0
		let _y0 = y0
		let _x1 = x1
		let _y1 = y1

		if (x1>x0) { x0 = x0 +shift_value; x1 = x1 -shift_value; }
		if (x1<x0) { x0 = x0 -shift_value; x1 = x1 +shift_value; }
		if (y1>y0) { y0 = y0 +shift_value; y1 = y1 -shift_value; }
		if (y1<y0) { y0 = y0 -shift_value; y1 = y1 +shift_value; }

		// last arrow to draw
		if (move.length == 0) {
			// special case for knights moves

			if (Math.abs(_x0-_x1) == 2 && Math.abs(_y0-_y1) == 1) {

				if (y1>y0) { y1 = y1 +shift_value; }
				if (y1<y0) { y1 = y1 -shift_value; }

				_drawArrow(x0, _y0, x1, y0, 15, 15, true)
				singleline = false
				x0 = x1
			}

			if (Math.abs(_x0-_x1) == 1 && Math.abs(_y0-_y1) == 2) {

				if (x1>x0) { x1 = x1 +shift_value; }
				if (x1<x0) { x1 = x1 -shift_value; }

				_drawArrow(_x0, y0, x0, y1, 15, 15, true)
				singleline = false
				y0 = y1
			}
		}

		_drawArrow(x0, y0, x1, y1, 15, 15, singleline)
	} while(move.length>4)
}


var ChessboardArrows = function (q, RES_FACTOR = 2) {

	const NUM_SQUARES = 8
	const DRAWING_CANVAS = 'drawing_canvas'+q.index
	const PRIMARY_CANVAS = 'primary_canvas'+q.index

	let index = q.index

	var resFactor = RES_FACTOR;

	// drawing canvas
	var drawCanvas = document.getElementById(DRAWING_CANVAS);
	var drawContext = changeResolution(drawCanvas, resFactor);

	// primary canvas
	var primaryCanvas = document.getElementById(PRIMARY_CANVAS);
	var primaryContext = changeResolution(primaryCanvas, resFactor);

	let id = 'board_wrapper'+index

	// setup mouse event callbacks
	let board = document.getElementById(id);
	board.addEventListener("mousedown", function(event) { onMouseDown(event); });
	board.addEventListener("mouseup", function(event) { onMouseUp(event); });
	board.addEventListener("mousemove", function(event) { onMouseMove(event); });
	board.addEventListener('contextmenu', function (event) { event.preventDefault(); }, false);

	// initialise vars
	var initialPoint = { x: null, y: null };
	var finalPoint = { x: null, y: null };

	var mouseDown = false;

	function getMousePos(canvas, e) {
		var rect = canvas.getBoundingClientRect();
		return {
			x: Q(e.clientX - rect.left),
			y: Q(e.clientY - rect.top),
			col: Math.floor((e.clientX - rect.left)*2/(primaryCanvas.width/NUM_SQUARES)) + 1,
			row: Math.floor((e.clientY - rect.top)*2/(primaryCanvas.width/NUM_SQUARES)) + 1,
		};
	}

	function setContextStyle(context, colour) {
		context.strokeStyle = context.fillStyle = colour;
		context.lineJoin = 'butt';
	}

	function onMouseDown(e) {
		if (e.which == 3) { // right click

			let value = 0

			if (e.shiftKey) value += 1
			if (e.ctrlKey) value += 2
			if (e.altKey) value += 4

			let color = ["green","yellow","red","white","DeepSkyBlue","black","orange"][value]

			mouseDown = true;
			initialPoint = finalPoint = getMousePos(drawCanvas, e);

			initialPoint.color = color

			Chessboard._drawSquare(DRAWING_CANVAS, Chessboard.toSquare(initialPoint.row, initialPoint.col), false, color)
		}
	}

	function onMouseMove(event) {
		finalPoint = getMousePos(drawCanvas, event);

		if (!mouseDown) return;
		if (initialPoint.x == finalPoint.x && initialPoint.y == finalPoint.y) return;

		drawContext.clearRect(0, 0, drawCanvas.width, drawCanvas.height);

		Chessboard._drawArrow(DRAWING_CANVAS, Chessboard.toSquare(initialPoint.row, initialPoint.col)+Chessboard.toSquare(finalPoint.row, finalPoint.col), false, initialPoint.color)
	}

	function onMouseUp(event) {

		if (event.which == 3) { // right click
			mouseDown = false;
			// if starting position == ending position, draw a circle to primary canvas
			if (initialPoint.x == finalPoint.x && initialPoint.y == finalPoint.y) {
				
				Chessboard._drawSquare(PRIMARY_CANVAS, Chessboard.toSquare(initialPoint.row, initialPoint.col), false, initialPoint.color)
			}
			// otherwise draw an arrow 
			else {
				Chessboard._drawArrow(PRIMARY_CANVAS, Chessboard.toSquare(initialPoint.row, initialPoint.col)+Chessboard.toSquare(finalPoint.row, finalPoint.col), false, initialPoint.color)
			}
			drawContext.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
		}
		else if (event.which == 1) { // left click
			clearCanvas();
		}
	}

	function clearCanvas() {
		// clear canvases
		drawContext.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
		primaryContext.clearRect(0, 0, primaryCanvas.width, primaryCanvas.height);
	}

	function Q(x) {  // mid-tread quantiser
		let d = primaryCanvas.width/(resFactor*NUM_SQUARES);
		return d*(Math.floor(x/d) + 0.5);
	}

	// source: https://stackoverflow.com/questions/14488849/higher-dpi-graphics-with-html5-canvas
	function changeResolution(canvas, scaleFactor) {
		// Set up CSS size.
		canvas.style.width = canvas.style.width || canvas.width + 'px';
		canvas.style.height = canvas.style.height || canvas.height + 'px';

		// Resize canvas and scale future draws.
		canvas.width = Math.ceil(canvas.width * scaleFactor);
		canvas.height = Math.ceil(canvas.height * scaleFactor);
		var ctx = canvas.getContext('2d');
		ctx.scale(scaleFactor, scaleFactor);
		return ctx;
	}
}