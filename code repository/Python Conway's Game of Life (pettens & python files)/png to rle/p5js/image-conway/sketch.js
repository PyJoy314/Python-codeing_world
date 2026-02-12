// holds the uploaded image
let img = new Image()
// output dimensions
let imageWidth = 80
let imageHeight = 80
// holds the resized image, not displayed on screen
let canvas
let context

// triggered on image upload
function loadFile(event) {
  // update img
  img.src = URL.createObjectURL(event.target.files[0])
  updateCanvas()
}

// called in loadFile and submit
function updateCanvas() {
  // draw resized image on fake canvas
  canvas = document.createElement('canvas')
  canvas.width = imageWidth
  canvas.height = imageHeight
  context = canvas.getContext('2d')
  // draw resized image
  context.drawImage(img, 0, 0, imageWidth, imageHeight)
}

function submit() {
  if(imageWidth > 0){
    imageWidth = parseInt($("#dotWidth").val())
  }
  if(imageHeight > 0){
    imageHeight = parseInt($("#dotHeight").val())
  }
  updateCanvas();
  updateGrid()
}

function getPixel(x, y) {
  return context.getImageData(x, y, 1, 1).data;
}

function getPixelArr() {
  // returns a 2d array of grayscale values
  // in range [0, 1)
  let ans = []
  for(let r = 0; r < imageHeight; r++){
    let row = []
    for(let c = 0; c < imageWidth; c++){
      let color = getPixel(c, r);
      let R = color[0]
      let G = color[1]
      let B = color[2]
      let avg = (R+G+B) / 3.0
      avg = avg / 256.0
      row.push(avg)
    }
    ans.push(row)
  }
  return ans
}

function dither(arr) {
  // arr is 2d list of grayscale values in range [0,1)
  function findClosestColor(color) {
    if (color < 0.5) {
      return 0
    } else {
      return 1
    }
  }
  // clone arr
  let copy = []
  for(let row of arr){
    copy.push(row.slice())
  }
  arr = copy
  
  let height = arr.length
  let width = arr[0].length
  
  for(let r = 0; r < imageHeight; r++){
    for(let c = 0; c < imageWidth; c++) {
      let oldPixel = arr[r][c]
      let newPixel = findClosestColor(oldPixel)
      arr[r][c] = newPixel
      let error = oldPixel - newPixel
      
      let right = c < imageWidth - 1
      let down = r < imageHeight - 1
      let left = c > 0
      
      if(right)
      arr[r][c+1] += error * 7.0/16
      if(right && down)
      arr[r+1][c+1] += error * 1.0/16
      if(down)
      arr[r+1][c] += error * 5.0/16
      if(left && down)
      arr[r+1][c-1] += error * 3.0/16 
    }
  }
  return arr
}


// 2D array of 0 | 1 -> 2D array of boolean
function ditheredToConway(arr) {
  return arr.map(row => row.map(px => !!px))
}

function conwayStep(arr) {
  return arr.map((row, r) => row.map((_, c) => cellStep(arr, r, c)))
}

function cellStep(arr, r, c) {
  const alive = arr[r][c]
  const numLivingNeighbors = getNumLivingNeighbors(arr, r, c)
  return numLivingNeighbors === 3 || (alive && numLivingNeighbors === 2)
}

function getNumLivingNeighbors(arr, r, c) {
  return getCell(arr, r - 1, c - 1) + getCell(arr, r - 1, c) + getCell(arr, r - 1, c + 1)
  + getCell(arr, r, c - 1) + getCell(arr, r, c + 1)
  + getCell(arr, r + 1, c - 1) + getCell(arr, r + 1, c) + getCell(arr, r + 1, c + 1)
}

// wraps around on out of bounds
function getCell(arr, r, c) {
  const width = arr[0].length
  const height = arr.length
  if (r < 0) r += height
  if (c < 0) c += width
  return arr[r % height][c % width]
}

let grid

function setup() {
  createCanvas(400, 400)
  noStroke()
  frameRate(20)
}

function draw() {
  if (grid) {
    const gridWidth = grid[0].length
    const gridHeight = grid.length
    const cellWidth = width / gridWidth
    const cellHeight = height / gridHeight
    for (let r = 0; r < gridHeight; r++) {
      for (let c = 0; c < gridWidth; c++) {
        if (grid[r][c]) {
          fill(255)
        } else {
          fill(0)
        }
        rect(c * cellWidth, r * cellHeight, cellWidth, cellHeight)
      }
    }
    grid = conwayStep(grid)
    console.log(grid)
  }
}

function updateGrid() {
  let arr = getPixelArr()
  let dithered = dither(arr)
  grid = ditheredToConway(dithered)
}
